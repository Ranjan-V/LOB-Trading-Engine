"""
Data Fetcher Module
Downloads historical market data from Binance API
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.data_config import *


class BinanceDataFetcher:
    """
    Fetches historical OHLCV data from Binance API
    No API key required for historical data
    """
    
    def __init__(self, symbol=DEFAULT_PAIR, interval=DEFAULT_INTERVAL):
        """
        Initialize data fetcher
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '1h')
        """
        self.symbol = symbol
        self.interval = interval
        self.base_url = BINANCE_BASE_URL + BINANCE_API_VERSION
        self.session = requests.Session()
        
        # Create data directories if they don't exist
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        os.makedirs(TICK_DATA_DIR, exist_ok=True)
        
        print(f"✅ BinanceDataFetcher initialized for {symbol} at {interval} interval")
    
    def fetch_klines(self, start_time=None, end_time=None, limit=MAX_ROWS_PER_REQUEST):
        """
        Fetch kline/candlestick data from Binance
        
        Args:
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of data points to fetch (max 1000)
            
        Returns:
            list: Raw kline data from API
        """
        endpoint = f"{self.base_url}/klines"
        
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = int(start_time)
        if end_time:
            params["endTime"] = int(end_time)
        
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Fetched {len(data)} candles")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching data: {e}")
            return None
    
    def fetch_historical_data(self, days=DEFAULT_LOOKBACK_DAYS):
        """
        Fetch historical data for specified number of days
        
        Args:
            days: Number of days to look back
            
        Returns:
            pd.DataFrame: Historical OHLCV data
        """
        print(f"\n📊 Fetching {days} days of historical data for {self.symbol}...")
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Convert to milliseconds
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        all_data = []
        current_start = start_ms
        
        # Fetch data in batches
        while current_start < end_ms:
            print(f"  Fetching batch starting from {datetime.fromtimestamp(current_start/1000)}")
            
            batch_data = self.fetch_klines(
                start_time=current_start,
                end_time=end_ms,
                limit=MAX_ROWS_PER_REQUEST
            )
            
            if not batch_data:
                print("  ⚠️ No data returned, stopping...")
                break
            
            all_data.extend(batch_data)
            
            # Update start time for next batch
            current_start = batch_data[-1][6] + 1  # Close time of last candle + 1ms
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
            
            # Check if we've reached the end
            if len(batch_data) < MAX_ROWS_PER_REQUEST:
                break
        
        print(f"\n✅ Total candles fetched: {len(all_data)}")
        
        # Convert to DataFrame
        if all_data:
            df = self._parse_klines(all_data)
            return df
        else:
            print("❌ No data fetched!")
            return None
    
    def _parse_klines(self, klines_data):
        """
        Parse raw kline data into pandas DataFrame
        
        Args:
            klines_data: Raw kline data from API
            
        Returns:
            pd.DataFrame: Parsed and formatted data
        """
        columns = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ]
        
        df = pd.DataFrame(klines_data, columns=columns)
        
        # Convert timestamps to datetime
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # Convert price/volume columns to float
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                          'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        df[numeric_columns] = df[numeric_columns].astype(float)
        
        # Convert trades to int
        df['trades'] = df['trades'].astype(int)
        
        # Drop the 'ignore' column
        df = df.drop('ignore', axis=1)
        
        # Sort by time
        df = df.sort_values('open_time').reset_index(drop=True)
        
        return df
    
    def save_data(self, df, filename=None):
        """
        Save data to CSV file
        
        Args:
            df: DataFrame to save
            filename: Custom filename (optional)
            
        Returns:
            str: Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.symbol}_{self.interval}_{timestamp}.csv"
        
        filepath = os.path.join(RAW_DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        
        print(f"\n💾 Data saved to: {filepath}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Date range: {df['open_time'].min()} to {df['open_time'].max()}")
        
        return filepath
    
    def get_latest_data(self, limit=100):
        """
        Get the most recent data points
        
        Args:
            limit: Number of recent candles to fetch
            
        Returns:
            pd.DataFrame: Recent data
        """
        print(f"\n📊 Fetching latest {limit} candles for {self.symbol}...")
        
        klines = self.fetch_klines(limit=limit)
        
        if klines:
            df = self._parse_klines(klines)
            print(f"✅ Fetched {len(df)} recent candles")
            return df
        else:
            return None
    
    def get_data_info(self, df):
        """
        Display information about the fetched data
        
        Args:
            df: DataFrame to analyze
        """
        print("\n" + "="*70)
        print("DATA INFORMATION")
        print("="*70)
        print(f"Symbol: {self.symbol}")
        print(f"Interval: {self.interval}")
        print(f"Total Rows: {len(df)}")
        print(f"Date Range: {df['open_time'].min()} to {df['open_time'].max()}")
        print(f"Duration: {(df['open_time'].max() - df['open_time'].min()).days} days")
        print(f"\nPrice Statistics:")
        print(f"  High: ${df['high'].max():,.2f}")
        print(f"  Low: ${df['low'].min():,.2f}")
        print(f"  Mean: ${df['close'].mean():,.2f}")
        print(f"  Latest: ${df['close'].iloc[-1]:,.2f}")
        print(f"\nVolume Statistics:")
        print(f"  Total Volume: {df['volume'].sum():,.2f}")
        print(f"  Average Volume: {df['volume'].mean():,.2f}")
        print(f"  Total Trades: {df['trades'].sum():,}")
        print("="*70)


def main():
    """
    Test the data fetcher
    """
    print("="*70)
    print("BINANCE DATA FETCHER - TEST RUN")
    print("="*70)
    
    # Initialize fetcher
    fetcher = BinanceDataFetcher(symbol="BTCUSDT", interval="1m")
    
    # Fetch 7 days of data
    df = fetcher.fetch_historical_data(days=7)
    
    if df is not None:
        # Display info
        fetcher.get_data_info(df)
        
        # Save data
        fetcher.save_data(df)
        
        print("\n✅ Data fetcher test completed successfully!")
    else:
        print("\n❌ Data fetcher test failed!")


if __name__ == "__main__":
    main()