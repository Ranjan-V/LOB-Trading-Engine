"""
Data Collection Configuration
Contains all settings for market data fetching and processing
"""

# Binance API Configuration
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_API_VERSION = "/api/v3"

# Trading Pairs to Download
TRADING_PAIRS = [
    "BTCUSDT",  # Bitcoin
    "ETHUSDT",  # Ethereum
    "BNBUSDT",  # Binance Coin
]

# Default trading pair for backtesting
DEFAULT_PAIR = "BTCUSDT"

# Time Intervals (Binance format)
INTERVALS = {
    "1m": "1m",      # 1 minute
    "5m": "5m",      # 5 minutes
    "15m": "15m",    # 15 minutes
    "1h": "1h",      # 1 hour
    "4h": "4h",      # 4 hours
    "1d": "1d",      # 1 day
}

# Default interval for data collection
DEFAULT_INTERVAL = "1m"

# Data Storage Paths
DATA_DIR = "data"
RAW_DATA_DIR = f"{DATA_DIR}/raw"
PROCESSED_DATA_DIR = f"{DATA_DIR}/processed"
TICK_DATA_DIR = f"{DATA_DIR}/tick_data"

# Data Collection Parameters
DEFAULT_LOOKBACK_DAYS = 30  # How many days of historical data to fetch
MAX_ROWS_PER_REQUEST = 1000  # Binance limit

# Data Processing Parameters
OUTLIER_THRESHOLD = 5.0  # Standard deviations for outlier detection
MIN_VOLUME_THRESHOLD = 0.0001  # Minimum volume to keep data point

# Tick Data Generation Parameters
TICK_GENERATION_METHOD = "poisson"  # Method to generate synthetic ticks
AVERAGE_TICKS_PER_MINUTE = 100  # Average tick frequency
LAMBDA_ARRIVAL_RATE = 1.67  # Poisson lambda (ticks per second)

# Order Flow Parameters
BUY_SELL_RATIO = 0.5  # Probability of buy order (0.5 = balanced)
ORDER_SIZE_MEAN = 1.0  # Mean order size
ORDER_SIZE_STD = 0.5   # Standard deviation of order size

# Data Validation Parameters
REQUIRED_COLUMNS = [
    "open_time",
    "open",
    "high", 
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "trades",
    "taker_buy_base",
    "taker_buy_quote",
]

# Column Renaming Map (Binance -> Our Format)
COLUMN_RENAME_MAP = {
    "open_time": "timestamp",
    "open": "open",
    "high": "high",
    "low": "low", 
    "close": "close",
    "volume": "volume",
    "close_time": "close_timestamp",
    "quote_volume": "quote_volume",
    "trades": "num_trades",
    "taker_buy_base": "taker_buy_volume",
    "taker_buy_quote": "taker_buy_quote_volume",
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API Rate Limiting
REQUEST_DELAY = 0.1  # Seconds between requests to avoid rate limits
MAX_RETRIES = 3      # Number of retries for failed requests

# Data Quality Checks
CHECK_FOR_GAPS = True
CHECK_FOR_DUPLICATES = True
CHECK_FOR_OUTLIERS = True

print("✅ Data configuration loaded successfully!")