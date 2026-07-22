# HYBE OpenDART·XBRL Pipeline

## 처리 흐름

1. 2023~2025년 연결재무제표 수집
2. 사업보고서 접수번호 검색
3. XBRL ZIP 다운로드 및 압축 해제
4. 추가 차원 없는 연결 기준 Context에서 Goodwill 추출
5. 11개 표준 계정 CSV 생성
6. 데이터 완전성 검증
7. Audit Red Flag Agent 실행
8. JSON 및 Markdown 보고서 생성

## 자동 추출 영업권

- 2023: 1,717,432,202,000원
- 2024: 1,809,808,639,000원
- 2025: 1,679,490,429,000원

## 최종 결과

- 결측값: 0
- Agent 종료 코드: 0
- Red Flag: 7
- Monitoring Signal: 3

## 범위

Agent 본체는 정해진 11개 계정 CSV에 대해 범용적으로 실행됩니다.
DART 및 XBRL 자동 수집 파이프라인은 현재 하이브 기준으로 검증됐습니다.
