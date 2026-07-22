from pathlib import Path
import pandas as pd
import subprocess
import sys

project_root = Path(__file__).resolve().parents[1]
agent_script = project_root / 'src' / 'generic_runtime_agent.py'
test_root = project_root / 'test_outputs' / 'invalid_inputs'
test_root.mkdir(parents=True, exist_ok=True)

base_rows = [
    ['Revenue', 1000000000000, 1100000000000, 1250000000000],
    ['Operating_Profit', 120000000000, 110000000000, 90000000000],
    ['Net_Income', 90000000000, 70000000000, 40000000000],
    ['Total_Assets', 1800000000000, 1950000000000, 2100000000000],
    ['Operating_Cash_Flow', 100000000000, 115000000000, 130000000000],
    ['Intangible_Assets', 180000000000, 200000000000, 220000000000],
    ['Goodwill', 350000000000, 360000000000, 370000000000],
    ['Investment_in_Associates', 120000000000, 110000000000, 95000000000],
    ['Accounts_Receivable', 100000000000, 130000000000, 180000000000],
    ['Inventory', 80000000000, 100000000000, 140000000000],
    ['Trade_Payables', 60000000000, 70000000000, 90000000000],
]

columns = ['Account', '2023', '2024', '2025']
tests = {}

tests['missing_account'] = pd.DataFrame(
    [row for row in base_rows if row[0] != 'Goodwill'],
    columns=columns,
)

tests['duplicate_account'] = pd.DataFrame(
    base_rows + [['Revenue', 999000000000, 999000000000, 999000000000]],
    columns=columns,
)

numeric_error_rows = [row.copy() for row in base_rows]
for row in numeric_error_rows:
    if row[0] == 'Net_Income':
        row[3] = '숫자아님'

tests['numeric_error'] = pd.DataFrame(
    numeric_error_rows,
    columns=columns,
)

failed_tests = []

for test_name, test_df in tests.items():
    input_csv = test_root / f'{test_name}.csv'
    output_dir = test_root / f'{test_name}_outputs'
    test_df.to_csv(input_csv, index=False, encoding='utf-8-sig')

    result = subprocess.run([
        sys.executable,
        str(agent_script),
        str(input_csv),
        '--company',
        f'테스트기업_{test_name}',
        '--output-dir',
        str(output_dir),
    ], capture_output=True, text=True)

    passed = result.returncode == 1
    print(test_name, 'PASS' if passed else 'FAIL', result.returncode)

    if not passed:
        failed_tests.append(test_name)

if failed_tests:
    raise SystemExit(f'실패한 테스트: {failed_tests}')

print('잘못된 입력 통제 테스트 PASS')