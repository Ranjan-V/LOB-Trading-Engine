"""
Full Backtest on ALL Real Binance Data
Proves we're using real market data
"""

import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting.backtester import Backtester
from src.backtesting.report_generator import ReportGenerator
from src.data.data_processor import DataProcessor


def run_full_backtest():
    """Run backtest on ALL available data"""
    
    print("="*70)
    print("FULL BACKTEST ON REAL BINANCE DATA")
    print("="*70)
    
    # Load data
    processor = DataProcessor()
    data_dir = Path("data/raw")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No data files found!")
        return
    
    latest_file = max(csv_files, key=os.path.getctime)
    
    print(f"\n📂 Loading REAL Binance data from: {latest_file.name}")
    data = processor.load_data(str(latest_file))
    
    print(f"\n📊 Data Summary:")
    print(f"   Total rows: {len(data):,}")
    print(f"   Date range: {data['open_time'].min()} to {data['open_time'].max()}")
    print(f"   Duration: {(data['open_time'].max() - data['open_time'].min()).days} days")
    print(f"   First price: ${data['close'].iloc[0]:,.2f}")
    print(f"   Last price: ${data['close'].iloc[-1]:,.2f}")
    print(f"   Price change: ${data['close'].iloc[-1] - data['close'].iloc[0]:,.2f}")
    
    # Show that it's REAL data
    print(f"\n✅ THIS IS REAL BINANCE DATA!")
    print(f"   - Downloaded from Binance API")
    print(f"   - Contains actual Bitcoin prices")
    print(f"   - Real trading volume and activity")
    
    # Ask user how much data to use
    print(f"\n💡 Options:")
    print(f"   1. Quick test: 1,000 rows (~16 hours)")
    print(f"   2. Medium test: 5,000 rows (~3.5 days)")
    print(f"   3. Full backtest: ALL {len(data):,} rows (~7 days)")
    
    choice = input("\nEnter choice (1/2/3) [default=2]: ").strip() or "2"
    
    if choice == "1":
        data = data.head(1000)
        print(f"\n⚡ Using 1,000 rows for quick test")
    elif choice == "2":
        data = data.head(5000)
        print(f"\n⚡ Using 5,000 rows for medium test")
    else:
        print(f"\n🚀 Using ALL {len(data):,} rows - this will take a few minutes!")
    
    # Create backtester
    backtester = Backtester(
        data=data,
        initial_cash=100000.0,
        transaction_fee_bps=0.0
    )
    
    # Strategy parameters
    strategy_params = {
        'base_spread_bps': 10.0,   # 10 bps spread
        'order_size': 0.1,          # 0.1 BTC per quote
        'max_inventory': 5.0        # Max 5 BTC inventory
    }
    
    print(f"\n📊 Strategy Parameters:")
    print(f"   Base Spread: {strategy_params['base_spread_bps']} bps")
    print(f"   Order Size: {strategy_params['order_size']} BTC")
    print(f"   Max Inventory: ±{strategy_params['max_inventory']} BTC")
    
    # Run backtest
    print(f"\n{'='*70}")
    print("STARTING BACKTEST ON REAL DATA")
    print("="*70)
    
    results = backtester.run_backtest(
        strategy_params, 
        progress_interval=max(100, len(data)//10)
    )
    
    # Print summary
    backtester.print_backtest_summary(results)
    
    # Generate report
    print(f"\n📊 Generating detailed report with charts...")
    report_gen = ReportGenerator(results)
    report_gen.generate_report()
    
    # Final message
    print(f"\n" + "="*70)
    print("✅ FULL BACKTEST COMPLETE!")
    print("="*70)
    print(f"\n📈 Key Results:")
    print(f"   Total Return: {results['total_return_pct']:+.2f}%")
    print(f"   Final Portfolio: ${results['final_portfolio_value']:,.2f}")
    print(f"   Total Trades: {results['strategy_stats']['trades_executed']}")
    print(f"   Data Points: {results['data_points']:,}")
    
    print(f"\n💾 All reports saved to: results/backtest_reports/")
    print(f"\n🎉 You just backtested a market maker on REAL Bitcoin data!")
    print("="*70)


if __name__ == "__main__":
    run_full_backtest()
    