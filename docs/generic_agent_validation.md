# Generic Agent Validation

## 검증 목적

generic_runtime_agent.py가 하이브에 종속되지 않고,
정해진 11개 표준 계정 형식의 다른 기업 데이터에도
작동하는지 확인했습니다.

## 정상 입력 테스트

- 기업: 샘플테크
- 종료 코드: 0
- Red Flag: 4
- Monitoring Signal: 6
- JSON 보고서 생성: PASS
- Markdown 보고서 생성: PASS

## 잘못된 입력 통제 테스트

- 필수 계정 누락: PASS
- 중복 계정: PASS
- 숫자 오류: PASS

## 검증 결론

Agent 본체는 정해진 11개 표준 계정 CSV 입력에 대해
기업명, 재무 규모, 재무 흐름이 달라도 실행됩니다.

OpenDART 및 XBRL 자동 수집은 현재 하이브 기준으로만
End-to-End 검증됐습니다.