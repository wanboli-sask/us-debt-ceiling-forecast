# US Debt Ceiling Forecast / 美国债务上限预测

2027年美国联邦债务上限预测仪表盘，支持每日数据更新、AI自适应权重学习与中英文双语界面。

## Features / 功能

- X-date cash-flow projection / X-date现金流预测
- 2027 vote window probabilities / 2027投票窗口概率
- ±15-day market impact forecast / 投票前后半个月市场冲击预测
- AI adaptive weight learning + manual override / AI权重自学习 + 手动调权
- Daily Treasury/FRED/market/news updates / 每日财政部/市场/新闻更新

## Quick Start / 快速开始

```bash
cd ~/Projects/us-debt-ceiling-forecast
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add FRED_API_KEY
streamlit run app.py
```

## Background Scheduler / 后台调度

```bash
python scheduler.py
```

## Baseline Predictions / 基线预测

| Event | Most Likely |
|-------|-------------|
| Debt limit hit | 2027-03-15 |
| X-date | 2027-10-01 |
| Final vote | 2027-09-28 |

## Disclaimer / 免责声明

This tool provides statistical model forecasts, not investment advice.
本工具为统计模型预测，非投资建议。

## Rebuild Historical Data

```bash
python scripts/build_historical_data.py
```

## 2023 Backtest / 回测验证

Dashboard page **Backtest Validation / 回测验证** or CLI:

```bash
python -c "from models.backtest import run_backtest_2023; run_backtest_2023()"
```

Report saved to `data/backtest_report.json`.

## FRED API Setup / 配置 FRED

1. Register free at https://fred.stlouisfed.org/docs/api/api_key.html
2. `cp .env.example .env` and set `FRED_API_KEY=your_32_char_key`
3. Verify: `python scripts/verify_daily_update.py`

Without a valid key, TGA/DGS10 use fallback values and the sidebar shows a warning.
