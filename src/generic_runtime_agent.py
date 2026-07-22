from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


YEARS = ["2023", "2024", "2025"]

REQUIRED_ACCOUNTS = [
    "Revenue",
    "Operating_Profit",
    "Net_Income",
    "Total_Assets",
    "Operating_Cash_Flow",
    "Intangible_Assets",
    "Goodwill",
    "Investment_in_Associates",
    "Accounts_Receivable",
    "Inventory",
    "Trade_Payables",
]

DISCLAIMER = (
    "식별된 Red Flag는 오류나 부정의 존재를 의미하는 것이 아니라, "
    "기업 및 환경에 대한 이해와 중요왜곡표시위험 평가를 위해 "
    "추가적인 질문과 검토가 필요한 영역을 의미한다."
)

ACCOUNT_ALIASES = {
    "Revenue": [
        "revenue", "sales", "매출액", "영업수익", "수익"
    ],
    "Operating_Profit": [
        "operatingprofit", "operatingincome",
        "영업이익", "영업손익"
    ],
    "Net_Income": [
        "netincome", "profitforperiod",
        "당기순이익", "당기순손익", "연결당기순이익"
    ],
    "Total_Assets": [
        "totalassets", "자산총계", "총자산"
    ],
    "Operating_Cash_Flow": [
        "operatingcashflow",
        "cashflowsfromoperatingactivities",
        "영업활동현금흐름",
        "영업활동으로인한현금흐름"
    ],
    "Intangible_Assets": [
        "intangibleassets", "무형자산"
    ],
    "Goodwill": [
        "goodwill", "영업권"
    ],
    "Investment_in_Associates": [
        "investmentinassociates",
        "investmentsinassociates",
        "관계기업투자",
        "관계기업투자주식",
        "관계기업및공동기업투자"
    ],
    "Accounts_Receivable": [
        "accountsreceivable",
        "tradereceivables",
        "매출채권",
        "매출채권및기타채권"
    ],
    "Inventory": [
        "inventory", "inventories", "재고자산"
    ],
    "Trade_Payables": [
        "tradepayables",
        "accountspayable",
        "매입채무",
        "매입채무및기타채무"
    ],
}

QUESTION_LIBRARY = {
    "RF-001": {
        "question": (
            "매출 성장에도 영업이익률이 하락한 주요 원인은 무엇이며, "
            "일시적 요인과 구조적 요인을 구분할 수 있습니까?"
        ),
        "evidence_request": (
            "부문별 손익자료, 원가 분석표, 주요 비용 증감명세"
        ),
    },
    "RF-002": {
        "question": (
            "영업이익 감소에도 영업현금흐름이 개선된 원인은 "
            "운전자본 변화, 비현금비용 또는 일회성 항목 중 무엇입니까?"
        ),
        "evidence_request": (
            "영업현금흐름 조정내역, 운전자본 증감표, 비현금항목 명세"
        ),
    },
    "RF-003": {
        "question": (
            "수익성 저하가 영업권이 배분된 현금창출단위의 "
            "손상검사 가정에 어떤 영향을 미쳤습니까?"
        ),
        "evidence_request": (
            "영업권 배분표, 손상검사 보고서, 사업계획과 할인율 산정자료"
        ),
    },
    "RF-004": {
        "question": (
            "매출채권 증가가 매출 성장보다 큰 경우, "
            "회수조건이나 연체채권 구성에 변화가 있었습니까?"
        ),
        "evidence_request": (
            "매출채권 연령분석표, 후속입금내역, 주요 고객별 잔액"
        ),
    },
    "RF-005": {
        "question": (
            "재고 증가가 매출 증가를 초과한 원인과 "
            "장기체화 또는 순실현가능가치 하락 가능성은 무엇입니까?"
        ),
        "evidence_request": (
            "재고 연령분석표, 판매실적, 평가충당금 산정자료"
        ),
    },
    "RF-006": {
        "question": (
            "영업이익이 흑자임에도 대규모 순손실이 발생한 "
            "비영업 항목의 구체적 구성은 무엇입니까?"
        ),
        "evidence_request": (
            "금융손익, 지분법손익, 손상차손 및 일회성 항목 명세"
        ),
    },
    "RF-007": {
        "question": (
            "관계기업투자 감소가 처분, 손상, 지분법손실 중 "
            "어떤 요인에서 발생했습니까?"
        ),
        "evidence_request": (
            "관계기업별 장부금액 변동표, 평가자료, 처분계약서"
        ),
    },
    "RF-008": {
        "question": (
            "2년 연속 영업이익률 하락의 핵심 원인과 "
            "향후 회복 계획의 실현 가능성을 어떻게 평가하고 있습니까?"
        ),
        "evidence_request": (
            "연도별 예산 대비 실적, 부문별 마진 분석, 향후 사업계획"
        ),
    },
    "RF-009": {
        "question": (
            "매출 성장에도 순손실이 지속된 원인과 "
            "손실의 반복 가능성은 어떻게 평가하고 있습니까?"
        ),
        "evidence_request": (
            "손실 원인 분석표, 비경상항목 명세, 향후 손익 전망"
        ),
    },
    "RF-010": {
        "question": (
            "자산 활용도는 개선됐지만 ROA가 음수인 원인이 "
            "영업외손실 또는 자산평가 문제와 관련되어 있습니까?"
        ),
        "evidence_request": (
            "자산별 수익성 분석, 손상검사 자료, 영업외손익 명세"
        ),
    },
}


def normalize_text(value: object) -> str:
    text = str(value).strip().lower()
    return re.sub(r"[\s_\-\(\)\[\]·,.]", "", text)


ALIAS_LOOKUP = {}

for standard_account, aliases in ACCOUNT_ALIASES.items():
    ALIAS_LOOKUP[normalize_text(standard_account)] = standard_account

    for alias in aliases:
        ALIAS_LOOKUP[normalize_text(alias)] = standard_account


def standardize_account_name(value: object) -> str | None:
    return ALIAS_LOOKUP.get(normalize_text(value))


def detect_account_column(data: pd.DataFrame) -> str:
    candidates = [
        "account",
        "account_name",
        "계정",
        "계정명",
        "과목",
        "과목명",
    ]

    normalized_columns = {
        normalize_text(column): column
        for column in data.columns
    }

    for candidate in candidates:
        key = normalize_text(candidate)

        if key in normalized_columns:
            return normalized_columns[key]

    raise ValueError(
        "계정명 열을 찾지 못했습니다. "
        "account 또는 계정명 열이 필요합니다."
    )


def parse_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("(", "-", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("−", "-", regex=False)
        .replace({"-": "0", "": None, "nan": None})
    )

    return pd.to_numeric(cleaned, errors="coerce")


def load_and_validate(input_path: Path) -> tuple[pd.DataFrame, dict]:
    data = pd.read_csv(input_path, encoding="utf-8-sig")
    data.columns = [str(column).strip() for column in data.columns]

    account_column = detect_account_column(data)

    missing_years = [
        year for year in YEARS
        if year not in data.columns
    ]

    if missing_years:
        raise ValueError(
            f"필수 연도 열이 없습니다: {missing_years}"
        )

    data["original_account"] = data[account_column].astype(str)
    data["account"] = data["original_account"].apply(
        standardize_account_name
    )

    for year in YEARS:
        data[year] = parse_numeric(data[year])

    recognized = data["account"].dropna().tolist()

    missing_accounts = [
        account for account in REQUIRED_ACCOUNTS
        if account not in recognized
    ]

    duplicate_accounts = (
        data.loc[data["account"].notna(), "account"]
        .value_counts()
    )

    duplicate_accounts = duplicate_accounts[
        duplicate_accounts > 1
    ].index.tolist()

    numeric_error_rows = data.loc[
        data["account"].notna()
        & data[YEARS].isna().any(axis=1)
    ]

    validation = {
        "source_file": input_path.name,
        "row_count": int(len(data)),
        "recognized_account_count": int(
            data["account"].notna().sum()
        ),
        "unrecognized_accounts": data.loc[
            data["account"].isna(),
            "original_account",
        ].tolist(),
        "missing_required_accounts": missing_accounts,
        "duplicate_accounts": duplicate_accounts,
        "numeric_error_row_count": int(len(numeric_error_rows)),
        "analysis_ready": bool(
            not missing_accounts
            and not duplicate_accounts
            and numeric_error_rows.empty
        ),
    }

    if not validation["analysis_ready"]:
        raise ValueError(
            "입력 데이터 검증 실패\n"
            + json.dumps(
                validation,
                ensure_ascii=False,
                indent=2,
            )
        )

    analysis_data = data.loc[
        data["account"].notna(),
        ["account", *YEARS],
    ].copy()

    return analysis_data, validation


def get_values(data: pd.DataFrame, account: str) -> dict:
    row = data.loc[data["account"] == account]

    if len(row) != 1:
        raise ValueError(
            f"{account} 계정은 정확히 한 행이어야 합니다."
        )

    return {
        year: float(row.iloc[0][year])
        for year in YEARS
    }


def growth_rate(current: float, previous: float) -> float | None:
    if previous == 0:
        return None

    return (current / previous - 1) * 100


def ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None

    return numerator / denominator * 100


def run_rules(data: pd.DataFrame) -> tuple[list, dict]:
    values = {
        account: get_values(data, account)
        for account in REQUIRED_ACCOUNTS
    }

    revenue = values["Revenue"]
    op = values["Operating_Profit"]
    net = values["Net_Income"]
    assets = values["Total_Assets"]
    ocf = values["Operating_Cash_Flow"]
    goodwill = values["Goodwill"]
    associates = values["Investment_in_Associates"]
    receivables = values["Accounts_Receivable"]
    inventory = values["Inventory"]

    metrics = {
        "revenue_growth_2025_pct": growth_rate(
            revenue["2025"], revenue["2024"]
        ),
        "receivables_growth_2025_pct": growth_rate(
            receivables["2025"], receivables["2024"]
        ),
        "inventory_growth_2025_pct": growth_rate(
            inventory["2025"], inventory["2024"]
        ),
        "operating_margin_2023_pct": ratio(
            op["2023"], revenue["2023"]
        ),
        "operating_margin_2024_pct": ratio(
            op["2024"], revenue["2024"]
        ),
        "operating_margin_2025_pct": ratio(
            op["2025"], revenue["2025"]
        ),
        "goodwill_to_assets_2025_pct": ratio(
            goodwill["2025"], assets["2025"]
        ),
        "roa_2025_pct": ratio(
            net["2025"], assets["2025"]
        ),
        "asset_turnover_2024": (
            revenue["2024"] / assets["2024"]
        ),
        "asset_turnover_2025": (
            revenue["2025"] / assets["2025"]
        ),
    }

    metrics["operating_margin_change_2025_ppt"] = (
        metrics["operating_margin_2025_pct"]
        - metrics["operating_margin_2024_pct"]
    )

    metrics["receivables_vs_revenue_gap_pct"] = (
        metrics["receivables_growth_2025_pct"]
        - metrics["revenue_growth_2025_pct"]
    )

    metrics["inventory_vs_revenue_gap_pct"] = (
        metrics["inventory_growth_2025_pct"]
        - metrics["revenue_growth_2025_pct"]
    )

    flags = [
        {
            "flag_id": "RF-001",
            "risk_family": "Profitability",
            "title": "외형 성장과 수익성 악화의 괴리",
            "triggered": (
                metrics["revenue_growth_2025_pct"] > 0
                and metrics[
                    "operating_margin_change_2025_ppt"
                ] <= -3
            ),
            "evidence": (
                f"매출 증가율 "
                f"{metrics['revenue_growth_2025_pct']:.1f}%, "
                f"영업이익률 변동 "
                f"{metrics['operating_margin_change_2025_ppt']:.1f}%p"
            ),
        },
        {
            "flag_id": "RF-002",
            "risk_family": "Cash Flow",
            "title": "이익과 영업현금흐름 방향의 불일치",
            "triggered": (
                op["2025"] < op["2024"]
                and ocf["2025"] > ocf["2024"]
            ),
            "evidence": (
                f"영업이익 {op['2024']:,.0f} → {op['2025']:,.0f}, "
                f"영업현금흐름 "
                f"{ocf['2024']:,.0f} → {ocf['2025']:,.0f}"
            ),
        },
        {
            "flag_id": "RF-003",
            "risk_family": "Impairment",
            "title": "높은 영업권 비중과 수익성 저하",
            "triggered": (
                metrics["goodwill_to_assets_2025_pct"] >= 20
                and metrics[
                    "operating_margin_change_2025_ppt"
                ] < 0
            ),
            "evidence": (
                f"영업권/총자산 "
                f"{metrics['goodwill_to_assets_2025_pct']:.1f}%, "
                f"영업이익률 변동 "
                f"{metrics['operating_margin_change_2025_ppt']:.1f}%p"
            ),
        },
        {
            "flag_id": "RF-004",
            "risk_family": "Receivables",
            "title": "매출 증가율 대비 매출채권 증가",
            "triggered": (
                metrics["receivables_vs_revenue_gap_pct"] >= 10
            ),
            "evidence": (
                f"매출채권 증가율 "
                f"{metrics['receivables_growth_2025_pct']:.1f}%, "
                f"매출 증가율 "
                f"{metrics['revenue_growth_2025_pct']:.1f}%"
            ),
        },
        {
            "flag_id": "RF-005",
            "risk_family": "Inventory",
            "title": "매출 증가율 대비 재고자산 증가",
            "triggered": (
                metrics["inventory_vs_revenue_gap_pct"] >= 10
            ),
            "evidence": (
                f"재고 증가율 "
                f"{metrics['inventory_growth_2025_pct']:.1f}%, "
                f"매출 증가율 "
                f"{metrics['revenue_growth_2025_pct']:.1f}%"
            ),
        },
        {
            "flag_id": "RF-006",
            "risk_family": "Earnings Quality",
            "title": "영업이익 흑자와 대규모 순손실의 괴리",
            "triggered": (
                op["2025"] > 0
                and net["2025"] < 0
                and abs(net["2025"]) > op["2025"]
            ),
            "evidence": (
                f"영업이익 {op['2025']:,.0f}, "
                f"당기순손익 {net['2025']:,.0f}"
            ),
        },
        {
            "flag_id": "RF-007",
            "risk_family": "Investments",
            "title": "관계기업투자 감소와 순손실 동시 발생",
            "triggered": (
                associates["2025"] < associates["2024"]
                and net["2025"] < 0
            ),
            "evidence": (
                f"관계기업투자 "
                f"{associates['2024']:,.0f} → "
                f"{associates['2025']:,.0f}, "
                f"당기순손익 {net['2025']:,.0f}"
            ),
        },
        {
            "flag_id": "RF-008",
            "risk_family": "Profitability",
            "title": "2년 연속 영업이익률 하락",
            "triggered": (
                metrics["operating_margin_2023_pct"]
                > metrics["operating_margin_2024_pct"]
                > metrics["operating_margin_2025_pct"]
            ),
            "evidence": (
                f"영업이익률 "
                f"{metrics['operating_margin_2023_pct']:.1f}% → "
                f"{metrics['operating_margin_2024_pct']:.1f}% → "
                f"{metrics['operating_margin_2025_pct']:.1f}%"
            ),
        },
        {
            "flag_id": "RF-009",
            "risk_family": "Loss Trend",
            "title": "매출 성장과 2개년 연속 순손실",
            "triggered": (
                revenue["2025"] > revenue["2024"]
                and net["2024"] < 0
                and net["2025"] < 0
            ),
            "evidence": (
                f"매출 {revenue['2024']:,.0f} → "
                f"{revenue['2025']:,.0f}, "
                f"순손익 {net['2024']:,.0f} → "
                f"{net['2025']:,.0f}"
            ),
        },
        {
            "flag_id": "RF-010",
            "risk_family": "Asset Efficiency",
            "title": "자산회전율 개선과 음의 ROA",
            "triggered": (
                metrics["asset_turnover_2025"]
                > metrics["asset_turnover_2024"]
                and metrics["roa_2025_pct"] < 0
            ),
            "evidence": (
                f"자산회전율 "
                f"{metrics['asset_turnover_2024']:.3f} → "
                f"{metrics['asset_turnover_2025']:.3f}, "
                f"ROA {metrics['roa_2025_pct']:.1f}%"
            ),
        },
    ]

    for flag in flags:
        item = QUESTION_LIBRARY[flag["flag_id"]]

        flag["triggered"] = bool(flag["triggered"])
        flag["status"] = (
            "Red Flag"
            if flag["triggered"]
            else "Monitoring Signal"
        )
        flag["interview_question"] = item["question"]
        flag["evidence_request"] = item["evidence_request"]
        flag["disclaimer"] = DISCLAIMER

    return flags, metrics


def select_top_3(flags: list) -> list:
    selected = []
    used_families = set()

    for flag in flags:
        if not flag["triggered"]:
            continue

        if flag["risk_family"] in used_families:
            continue

        selected.append(flag)
        used_families.add(flag["risk_family"])

        if len(selected) == 3:
            break

    return selected


def save_results(
    company: str,
    source_file: str,
    validation: dict,
    flags: list,
    metrics: dict,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    red_flags = [
        flag for flag in flags
        if flag["triggered"]
    ]

    monitoring = [
        flag for flag in flags
        if not flag["triggered"]
    ]

    top_3 = select_top_3(flags)

    result = {
        "company": company,
        "source_file": source_file,
        "analysis_period": "2023-2025",
        "validation": validation,
        "metrics": metrics,
        "rule_count": len(flags),
        "red_flag_count": len(red_flags),
        "monitoring_signal_count": len(monitoring),
        "top_3": top_3,
        "all_results": flags,
        "disclaimer": DISCLAIMER,
    }

    json_path = output_dir / "runtime_audit_analysis.json"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    lines = [
        f"# {company} Audit Red Flag Report",
        "",
        f"- 입력파일: {source_file}",
        f"- 분석기간: 2023-2025",
        f"- 전체 규칙: {len(flags)}개",
        f"- Red Flag: {len(red_flags)}개",
        f"- Monitoring Signal: {len(monitoring)}개",
        "",
        "## Top 3 우선 검토 영역",
        "",
    ]

    for index, flag in enumerate(top_3, start=1):
        lines.extend([
            f"### {index}. {flag['title']}",
            "",
            f"- 위험군: {flag['risk_family']}",
            f"- 근거: {flag['evidence']}",
            f"- 인터뷰 질문: {flag['interview_question']}",
            f"- 요청 증빙: {flag['evidence_request']}",
            "",
        ])

    lines.extend([
        "## 주의사항",
        "",
        DISCLAIMER,
        "",
    ])

    markdown_path = output_dir / "runtime_audit_report.md"

    with markdown_path.open("w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return json_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "표준 CSV 재무데이터를 분석해 감사 Red Flag와 "
            "인터뷰 질문을 생성합니다."
        )
    )

    parser.add_argument(
        "input_csv",
        help="분석할 CSV 파일 경로",
    )

    parser.add_argument(
        "--company",
        default=None,
        help="기업명. 생략하면 CSV의 company 열 또는 파일명을 사용합니다.",
    )

    parser.add_argument(
        "--output-dir",
        default="runtime_outputs",
        help="결과 저장 폴더",
    )

    args = parser.parse_args()

    input_path = Path(args.input_csv)

    if not input_path.exists():
        raise FileNotFoundError(
            f"입력 파일을 찾을 수 없습니다: {input_path}"
        )

    original_data = pd.read_csv(
        input_path,
        encoding="utf-8-sig",
    )

    if args.company:
        company = args.company
    elif (
        "company" in original_data.columns
        and not original_data["company"].dropna().empty
    ):
        company = str(
            original_data["company"].dropna().iloc[0]
        )
    else:
        company = input_path.stem

    analysis_data, validation = load_and_validate(input_path)
    flags, metrics = run_rules(analysis_data)

    json_path, markdown_path = save_results(
        company=company,
        source_file=input_path.name,
        validation=validation,
        flags=flags,
        metrics=metrics,
        output_dir=Path(args.output_dir),
    )

    red_flag_count = sum(
        flag["triggered"] for flag in flags
    )

    print("분석 완료")
    print("기업:", company)
    print("Red Flag:", red_flag_count)
    print("Monitoring Signal:", len(flags) - red_flag_count)
    print("JSON:", json_path)
    print("보고서:", markdown_path)


if __name__ == "__main__":
    main()
