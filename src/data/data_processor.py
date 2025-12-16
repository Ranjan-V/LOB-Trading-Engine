"""
Data Processor Module
Cleans, validates, and processes raw market data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.data_config import *


class DataProcessor:
    """
    Processes and cleans market data for backtesting
    """
    
    def __init__(self):
        """Initialize data processor"""
        print("✅ DataProcessor initialized")
    
    def load_data(self, filepath):
        """
        Load data from CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            pd.DataFrame: Loaded data
        """
        print(f"\n📂 Loading data from: {filepath}")
        
        try:
            df = pd.read_csv(filepath)
            
            # Parse datetime columns
            if 'open_time' in df.columns:
                df['open_time'] = pd.to_datetime(df['open_time'])
            if 'close_time' in df.columns:
                df['close_time'] = pd.to_datetime(df['close_time'])
            
            print(f"✅ Loaded {len(df)} rows")
            return df
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def validate_data(self, df):
        """
        Validate data quality and structure
        
        Args:
            df: DataFrame to validate
            
        Returns:
            tuple: (is_valid, issues_list)
        """
        print("\n🔍 Validating data...")
        
        issues = []
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            issues.append(f"Missing values found: {missing[missing > 0].to_dict()}")
        
        # Check for duplicate timestamps
        if CHECK_FOR_DUPLICATES:
            duplicates = df.duplicated(subset=['open_time']).sum()
            if duplicates > 0:
                issues.append(f"Duplicate timestamps: {duplicates}")
        
        # Check for negative values
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                negatives = (df[col] < 0).sum()
                if negatives > 0:
                    issues.append(f"Negative values in {col}: {negatives}")
        
        # Check price consistency (high >= low, etc.)
        if all(col in df.columns for col in ['high', 'low', 'open', 'close']):
            invalid_high_low = (df['high'] < df['low']).sum()
            if invalid_high_low > 0:
                issues.append(f"Invalid high/low: {invalid_high_low}")
            
            invalid_open = ((df['open'] > df['high']) | (df['open'] < df['low'])).sum()
            if invalid_open > 0:
                issues.append(f"Open outside high/low range: {invalid_open}")
            
            invalid_close = ((df['close'] > df['high']) | (df['close'] < df['low'])).sum()
            if invalid_close > 0:
                issues.append(f"Close outside high/low range: {invalid_close}")
        
        # Check for gaps in time series
        if CHECK_FOR_GAPS and 'open_time' in df.columns:
            df_sorted = df.sort_values('open_time')
            time_diffs = df_sorted['open_time'].diff()
            expected_diff = pd.Timedelta(minutes=1)  # For 1m data
            
            gaps = (time_diffs > expected_diff * 1.5).sum()
            if gaps > 0:
                issues.append(f"Time gaps detected: {gaps}")
        
        is_valid = len(issues) == 0
        
        if is_valid:
            print("✅ Data validation passed!")
        else:
            print("⚠️ Data validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        return is_valid, issues
    
    def remove_outliers(self, df, column='close', threshold=OUTLIER_THRESHOLD):
        """
        Remove outliers using z-score method
        
        Args:
            df: DataFrame
            column: Column to check for outliers
            threshold: Z-score threshold
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        if not CHECK_FOR_OUTLIERS:
            return df
        
        print(f"\n🔍 Checking for outliers in {column} (threshold={threshold})...")
        
        initial_len = len(df)
        
        # Calculate z-scores
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        
        # Filter outliers
        df_clean = df[z_scores < threshold].copy()
        
        removed = initial_len - len(df_clean)
        
        if removed > 0:
            print(f"⚠️ Removed {removed} outliers ({removed/initial_len*100:.2f}%)")
        else:
            print(f"✅ No outliers detected")
        
        return df_clean
    
    def fill_missing_data(self, df):
        """
        Fill missing data points using forward fill
        
        Args:
            df: DataFrame with missing values
            
        Returns:
            pd.DataFrame: Data with filled values
        """
        print("\n🔧 Filling missing data...")
        
        initial_missing = df.isnull().sum().sum()
        
        if initial_missing == 0:
            print("✅ No missing data to fill")
            return df
        
        # Forward fill then backward fill
        df_filled = df.fillna(method='ffill').fillna(method='bfill')
        
        final_missing = df_filled.isnull().sum().sum()
        filled = initial_missing - final_missing
        
        print(f"✅ Filled {filled} missing values")
        
        return df_filled
    
    def add_technical_indicators(self, df):
        """
        Add common technical indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            pd.DataFrame: Data with added indicators
        """
        print("\n📊 Adding technical indicators...")
        
        df = df.copy()
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential moving averages
        df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Volatility (rolling standard deviation)
        df['volatility_10'] = df['returns'].rolling(window=10).std()
        df['volatility_50'] = df['returns'].rolling(window=50).std()
        
        # Volume indicators
        df['volume_sma_10'] = df['volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_10']
        
        # Price range
        df['high_low_range'] = df['high'] - df['low']
        df['open_close_range'] = abs(df['open'] - df['close'])
        
        # Bid-ask spread proxy (high - low as percentage of close)
        df['spread_pct'] = (df['high'] - df['low']) / df['close'] * 100
        
        print(f"✅ Added {len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']])} indicators")
        
        return df
    
    def resample_data(self, df, target_interval='5m'):
        """
        Resample data to different time interval
        
        Args:
            df: DataFrame with datetime index
            target_interval: Target interval (e.g., '5m', '1h')
            
        Returns:
            pd.DataFrame: Resampled data
        """
        print(f"\n🔄 Resampling data to {target_interval}...")
        
        df = df.copy()
        df = df.set_index('open_time')
        
        # Resample OHLCV data
        resampled = df.resample(target_interval).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'trades': 'sum',
            'quote_volume': 'sum',
        })
        
        resampled = resampled.dropna()
        resampled = resampled.reset_index()
        
        print(f"✅ Resampled from {len(df)} to {len(resampled)} rows")
        
        return resampled
    
    def process_pipeline(self, df, add_indicators=True, remove_outliers_flag=True):
        """
        Complete processing pipeline
        
        Args:
            df: Raw DataFrame
            add_indicators: Whether to add technical indicators
            remove_outliers_flag: Whether to remove outliers
            
        Returns:
            pd.DataFrame: Fully processed data
        """
        print("\n" + "="*70)
        print("DATA PROCESSING PIPELINE")
        print("="*70)
        
        # Validate
        is_valid, issues = self.validate_data(df)
        
        # Fill missing data
        df = self.fill_missing_data(df)
        
        # Remove outliers
        if remove_outliers_flag:
            df = self.remove_outliers(df)
        
        # Add technical indicators
        if add_indicators:
            df = self.add_technical_indicators(df)
        
        # Final validation
        is_valid, issues = self.validate_data(df)
        
        print("\n✅ Processing pipeline completed!")
        print(f"   Final rows: {len(df)}")
        print(f"   Final columns: {len(df.columns)}")
        
        return df
    
    def save_processed_data(self, df, filename):
        """
        Save processed data
        
        Args:
            df: Processed DataFrame
            filename: Output filename
            
        Returns:
            str: Path to saved file
        """
        filepath = os.path.join(PROCESSED_DATA_DIR, filename)
        df.to_csv(filepath, index=False)
        
        print(f"\n💾 Processed data saved to: {filepath}")
        
        return filepath
    
    def get_data_summary(self, df):
        """
        Generate summary statistics
        
        Args:
            df: DataFrame to summarize
        """
        print("\n" + "="*70)
        print("DATA SUMMARY")
        print("="*70)
        print(df.describe())
        print("\nColumns:", df.columns.tolist())
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print("="*70)


def main():
    """
    Test the data processor
    """
    print("="*70)
    print("DATA PROCESSOR - TEST RUN")
    print("="*70)
    
    # This is a placeholder test
    # In real usage, you would load data from data_fetcher
    print("\n✅ Data processor module loaded successfully!")
    print("   Use with data_fetcher to process downloaded data")
    
    processor = DataProcessor()
    print("\n✅ Ready to process data!")


if __name__ == "__main__":
    main()