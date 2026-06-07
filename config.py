from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "db" / "forecast.db"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

DEBT_LIMIT_TRILLIONS = 41.104
DEBT_LIMIT_DOLLARS = DEBT_LIMIT_TRILLIONS * 1e12

ANNUAL_DEFICIT_BILLIONS = 1800
DAILY_DEFICIT_DOLLARS = ANNUAL_DEFICIT_BILLIONS * 1e9 / 365

EM_HEADROOM_BILLIONS = 500
BUFFER_BILLIONS = 50

MARKET_WINDOW_DAYS = 15

DEFAULT_WEIGHTS = {
    "historical": 0.40,
    "sentiment": 0.35,
    "microstructure": 0.25,
}

WEIGHT_MIN = 0.05
WEIGHT_MAX = 0.70
HEDGE_ETA = 0.3
MAX_DAILY_WEIGHT_SHIFT = 0.05

NEWS_KEYWORDS = [
    "debt ceiling", "debt limit", "x-date", "x date", "default",
    "treasury", "extraordinary measures", "债务上限", "违约",
]

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=US+debt+ceiling&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=treasury+debt+limit&hl=en-US&gl=US&ceid=US:en",
]

TREASURY_DEBT_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    "v2/accounting/od/debt_to_penny"
)
TREASURY_CASH_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    "v1/accounting/dts/operating_cash_balance"
)
