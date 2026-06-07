# US Debt Ceiling Forecast

A bilingual Streamlit dashboard that forecasts the **2027 US federal debt ceiling** timeline — X-date, congressional vote windows, and market impact — using historical bipartisan patterns (2002–2025), live Treasury/FRED/market data, and news sentiment.

**Repository:** https://github.com/wanboli-sask/us-debt-ceiling-forecast

## Overview

This project combines cash-flow modeling, vote-timing heuristics, and market-impact regression to produce daily-updated forecasts for the next debt-ceiling cycle. The dashboard supports English and Chinese UI text and includes an adaptive weight learner that can be manually overridden.

> **Note:** All outputs are statistical model forecasts for research and education. They are **not** investment advice.

## Features

### Dashboard pages

| Page | Description |
|------|-------------|
| **Overview** | X-date countdown, sentiment score, risk level, debt headroom, VIX fear index |
| **Timeline** | 2027 vote windows with probability weights |
| **Market Impact** | ±15-day forecast curves for SPX, TLT, 10Y yield, and VIX around the vote |
| **Daily Report** | Snapshot history from the SQLite database |
| **Scenario** | Adjust deficit multiplier and extraordinary-measures headroom |
| **Weights** | AI adaptive weights with manual override sliders |
| **History** | 15 debt-limit episodes (2002–2025) with market metrics |
| **Backtest** | 2023 debt-ceiling validation results |

### Core capabilities

- **X-date projection** — Cash-flow model using debt outstanding, TGA balance, deficit assumptions, and extraordinary measures
- **Vote window probabilities** — Four 2027 windows derived from historical brinkmanship patterns
- **Market impact model** — ±15-day SPX / TLT / DGS10 / VIX curves weighted by history, sentiment, and microstructure signals
- **AI weight learning** — Online adjustment of model weights with user override support
- **Daily data pipeline** — Treasury Fiscal Data, FRED (TGA, DGS10, VIX), yfinance prices, RSS news + VADER sentiment
- **Bilingual UI** — Locale strings in `locales/en.json` and `locales/zh.json`

## Baseline 2027 predictions

| Event | Most likely | Range |
|-------|-------------|-------|
| Debt limit hit | 2027-03-15 | 2027-02-15 ~ 2027-06-30 |
| X-date | 2027-10-01 | 2027-09-01 ~ 2027-11-15 |
| Final vote | 2027-09-28 | 2027-09-15 ~ 2027-10-10 |

Vote window probabilities (from `data/baseline_2027.json`):

| Window | Period | Probability |
|--------|--------|-------------|
| Q1 procedural | 2027-02-20 ~ 2027-03-15 | 15% |
| Mid-year temporary | 2027-06-15 ~ 2027-07-31 | 20% |
| Fall brinkmanship | 2027-09-15 ~ 2027-10-10 | 55% |
| Post-default emergency | 2027-10-15 ~ 2027-11-30 | 10% |

## Tech stack

| Layer | Tools |
|-------|-------|
| UI | Streamlit, Plotly |
| Models | NumPy, pandas, scikit-learn |
| Data | yfinance, FRED API, Treasury Fiscal Data API, RSS + VADER |
| Storage | SQLite (`db/forecast.db`) |
| Scheduling | APScheduler |

## Project layout

```
us-debt-ceiling-forecast/
├── app.py                  # Streamlit entry point (8 pages)
├── config.py               # Paths and constants
├── models/                 # X-date, vote, market, weight learner, backtest
├── services/               # Treasury, FRED, market, news clients
├── components/             # Dashboard UI modules
├── jobs/daily_update.py    # Daily snapshot pipeline
├── scheduler.py            # Background daily scheduler
├── db/database.py          # SQLite helpers
├── data/                   # Historical votes, baseline, backtest report
├── locales/                # en.json / zh.json i18n strings
├── i18n/                   # Bilingual helper
└── scripts/                # Data build and verification utilities
```

## Quick start

```bash
git clone https://github.com/wanboli-sask/us-debt-ceiling-forecast.git
cd us-debt-ceiling-forecast
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional: add FRED_API_KEY
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Configuration

### FRED API key (recommended)

1. Register a free key at https://fred.stlouisfed.org/docs/api/api_key.html
2. Copy the example env file and paste your 32-character key:

```bash
cp .env.example .env
# Edit .env: FRED_API_KEY=your_32_char_key
```

3. Verify the pipeline:

```bash
python scripts/verify_daily_update.py
```

Without a valid key, TGA and DGS10 fall back to default values and the sidebar shows a warning. The app still runs using Treasury and yfinance data.

## Daily update pipeline

| Method | Command / action |
|--------|------------------|
| In-app | Click **Run Daily Update** in the sidebar |
| One-shot | `python jobs/daily_update.py` |
| Scheduler | `python scheduler.py` |
| Verify | `python scripts/verify_daily_update.py` |

Snapshots are stored in SQLite and logged to `logs/daily_update.log`.

## 2023 backtest

The model is validated against the 2023 debt-ceiling episode. Open the **Backtest** page in the dashboard, or run:

```bash
python -c "from models.backtest import run_backtest_2023; run_backtest_2023()"
```

Results are saved to `data/backtest_report.json`.

| Metric | Result |
|--------|--------|
| X-date MAE | 8.3 days |
| Final X-date error | −1 day (predicted 2023-06-04 vs actual 2023-06-05) |
| SPX direction (pre-vote) | Correct |
| Within confidence band | Yes |

## Utility scripts

```bash
# Rebuild historical dataset (15 episodes, CRS + yfinance metrics)
python scripts/build_historical_data.py

# Verify daily update end-to-end
python scripts/verify_daily_update.py
```

## Disclaimer

This tool provides **statistical model forecasts** based on historical patterns and publicly available data. Predictions involve significant uncertainty. Past performance in backtests does not guarantee future accuracy. **This is not investment advice.** Consult qualified professionals before making financial decisions.

---

# 中文文档

# 美国债务上限预测

一个双语 Streamlit 仪表盘，基于历史两党博弈规律（2002–2025）、实时财政部/FRED/市场数据及新闻情绪，预测 **2027 年美国联邦债务上限** 时间线——包括 X-date（违约风险日）、国会投票窗口及市场冲击。

**代码仓库：** https://github.com/wanboli-sask/us-debt-ceiling-forecast

## 项目简介

本项目将现金流建模、投票时机启发式规则与市场冲击回归相结合，为下一轮债务上限周期提供每日更新的预测。仪表盘支持中英文界面，并内置可手动覆盖的 AI 自适应权重学习模块。

> **提示：** 所有输出均为统计模型预测，仅供研究与学习参考，**不构成投资建议**。

## 功能特性

### 仪表盘页面

| 页面 | 说明 |
|------|------|
| **总览** | X-date 倒计时、情绪分数、风险等级、债务剩余额度、VIX 恐慌指数 |
| **时间线** | 2027 年各投票窗口及概率权重 |
| **市场冲击** | 投票前后 ±15 日 SPX、TLT、10 年期收益率、VIX 预测曲线 |
| **每日报告** | SQLite 数据库中的历史快照 |
| **情景分析** | 调整赤字倍数与非常规措施（EM）额度 |
| **权重调节** | AI 自适应权重 + 手动滑块覆盖 |
| **历史案例** | 15 次债务上限事件（2002–2025）及市场指标 |
| **回测验证** | 2023 年债务上限情景验证结果 |

### 核心能力

- **X-date 预测** — 基于债务余额、财政部账户（TGA）、赤字假设及非常规措施的现金流模型
- **投票窗口概率** — 四个 2027 年窗口，源自历史边缘博弈规律
- **市场冲击模型** — 投票前后 ±15 日 SPX / TLT / DGS10 / VIX 曲线，综合历史、情绪与微观结构信号加权
- **AI 权重学习** — 在线调整模型权重，支持用户手动覆盖
- **每日数据流水线** — 财政部财政数据、FRED（TGA、DGS10、VIX）、yfinance 行情、RSS 新闻 + VADER 情绪分析
- **双语界面** — 文案位于 `locales/en.json` 与 `locales/zh.json`

## 2027 基线预测

| 事件 | 最可能日期 | 区间 |
|------|-----------|------|
| 触及债务上限 | 2027-03-15 | 2027-02-15 ~ 2027-06-30 |
| X-date（违约风险日） | 2027-10-01 | 2027-09-01 ~ 2027-11-15 |
| 最终投票 | 2027-09-28 | 2027-09-15 ~ 2027-10-10 |

投票窗口概率（来源：`data/baseline_2027.json`）：

| 窗口 | 时间段 | 概率 |
|------|--------|------|
| 年初程序性投票 | 2027-02-20 ~ 2027-03-15 | 15% |
| 中期临时方案 | 2027-06-15 ~ 2027-07-31 | 20% |
| 秋季边缘博弈 | 2027-09-15 ~ 2027-10-10 | 55% |
| 违约后紧急立法 | 2027-10-15 ~ 2027-11-30 | 10% |

## 技术栈

| 层级 | 工具 |
|------|------|
| 界面 | Streamlit、Plotly |
| 模型 | NumPy、pandas、scikit-learn |
| 数据 | yfinance、FRED API、财政部财政数据 API、RSS + VADER |
| 存储 | SQLite（`db/forecast.db`） |
| 调度 | APScheduler |

## 项目结构

```
us-debt-ceiling-forecast/
├── app.py                  # Streamlit 入口（8 个页面）
├── config.py               # 路径与常量
├── models/                 # X-date、投票、市场、权重学习、回测
├── services/               # 财政部、FRED、市场、新闻客户端
├── components/             # 仪表盘 UI 组件
├── jobs/daily_update.py    # 每日快照流水线
├── scheduler.py            # 后台每日调度器
├── db/database.py          # SQLite 工具
├── data/                   # 历史投票、基线预测、回测报告
├── locales/                # en.json / zh.json 国际化文案
├── i18n/                   # 双语辅助函数
└── scripts/                # 数据构建与验证脚本
```

## 快速开始

```bash
git clone https://github.com/wanboli-sask/us-debt-ceiling-forecast.git
cd us-debt-ceiling-forecast
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # 可选：填入 FRED_API_KEY
streamlit run app.py
```

在浏览器中打开 http://localhost:8501 。

## 配置说明

### FRED API 密钥（推荐）

1. 在 https://fred.stlouisfed.org/docs/api/api_key.html 免费注册
2. 复制环境变量模板并填入 32 位密钥：

```bash
cp .env.example .env
# 编辑 .env：FRED_API_KEY=your_32_char_key
```

3. 验证流水线：

```bash
python scripts/verify_daily_update.py
```

未配置有效密钥时，TGA 和 DGS10 将使用回退默认值，侧边栏会显示警告。应用仍可借助财政部和 yfinance 数据正常运行。

## 每日更新流水线

| 方式 | 命令 / 操作 |
|------|------------|
| 应用内 | 点击侧边栏 **运行每日更新** |
| 单次执行 | `python jobs/daily_update.py` |
| 后台调度 | `python scheduler.py` |
| 验证 | `python scripts/verify_daily_update.py` |

快照存入 SQLite，日志写入 `logs/daily_update.log`。

## 2023 年回测

模型以 2023 年债务上限事件进行验证。在仪表盘打开 **回测验证** 页面，或运行：

```bash
python -c "from models.backtest import run_backtest_2023; run_backtest_2023()"
```

结果保存至 `data/backtest_report.json`。

| 指标 | 结果 |
|------|------|
| X-date 平均绝对误差 | 8.3 天 |
| 最终 X-date 误差 | −1 天（预测 2023-06-04，实际 2023-06-05） |
| 标普方向（投票前） | 正确 |
| 落在置信区间内 | 是 |

## 工具脚本

```bash
# 重建历史数据集（15 次事件，CRS + yfinance 指标）
python scripts/build_historical_data.py

# 端到端验证每日更新
python scripts/verify_daily_update.py
```

## 免责声明

本工具基于历史规律与公开数据提供 **统计模型预测**，存在显著不确定性。回测表现不代表未来准确性。**本工具不构成投资建议。** 做出财务决策前请咨询专业人士。
