"""
Quick Data Viewer - Inspect downloaded market data
"""

import pandas as pd
import os
from pathlib import Path

def view_latest_data():
    """View the most recently downloaded data file"""
    
    data_dir = Path("data/raw")
    
    # Get all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No data files found in data/raw/")
        return
    
    # Get most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    
    print("="*70)
    print("DATA VIEWER - LATEST DOWNLOADED DATA")
    print("="*70)
    print(f"\n📂 File: {latest_file.name}")
    print(f"📅 Modified: {pd.to_datetime(os.path.getmtime(latest_file), unit='s')}")
    
    # Load data
    df = pd.read_csv(latest_file)
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['close_time'] = pd.to_datetime(df['close_time'])
    
    print(f"\n📊 Data Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"📅 Date Range: {df['open_time'].min()} to {df['open_time'].max()}")
    print(f"⏱️  Duration: {(df['open_time'].max() - df['open_time'].min()).days} days")
    
    print("\n" + "="*70)
    print("FIRST 10 ROWS")
    print("="*70)
    print(df.head(10).to_string())
    
    print("\n" + "="*70)
    print("LAST 10 ROWS")
    print("="*70)
    print(df.tail(10).to_string())
    
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    print(f"\n💰 Price Statistics:")
    print(f"   Highest: ${df['high'].max():,.2f}")
    print(f"   Lowest:  ${df['low'].min():,.2f}")
    print(f"   Average: ${df['close'].mean():,.2f}")
    print(f"   Latest:  ${df['close'].iloc[-1]:,.2f}")
    
    print(f"\n📈 Volume Statistics:")
    print(f"   Total Volume: {df['volume'].sum():,.2f} BTC")
    print(f"   Average Volume: {df['volume'].mean():,.4f} BTC")
    print(f"   Total Trades: {df['trades'].sum():,}")
    
    print(f"\n📊 Data Quality:")
    print(f"   Missing Values: {df.isnull().sum().sum()}")
    print(f"   Duplicate Rows: {df.duplicated().sum()}")
    
    print("\n" + "="*70)
    print("✅ Data looks good! Ready for Order Book Engine!")
    print("="*70)

if __name__ == "__main__":
    view_latest_data()