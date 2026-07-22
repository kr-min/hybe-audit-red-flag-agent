from pathlib import Path
import pandas as pd
import subprocess
import sys

project_root = Path(__file__).resolve().parents[1]
agent_script = project_root / 'src' / 'generic_runtime_agent.py'
test_root = project_root / 'test_outputs'
test_root.mkdir(parents=True, exist_ok=True)

input_csv = test_root / 'sample_company_normal.csv'
output_dir = test_root / 'sample_company_normal_outputs'

test_df = pd.DataFrame([
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
], columns=['Account', '2023', '2024', '2025'])

test_df.to_csv(input_csv, index=False, encoding='utf-8-sig')

result = subprocess.run([
    sys.executable,
    str(agent_script),
    str(input_csv),
    '--company',
    '샘플테크',
    '--output-dir',
    str(output_dir),
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)

if result.returncode != 0:
    raise SystemExit(f'정상 입력 테스트 실패: {result.returncode}')

if 'Red Flag: 4' not in result.stdout:
    raise SystemExit('Red Flag 개수 불일치')

if 'Monitoring Signal: 6' not in result.stdout:
    raise SystemExit('Monitoring Signal 개수 불일치')

print('정상 입력 범용성 테스트 PASS')