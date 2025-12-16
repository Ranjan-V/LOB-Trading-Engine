"""
Backtesting Engine
Replays historical data and simulates strategy execution
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orderbook.orderbook import OrderBook
from src.orderbook.matching_engine import MatchingEngine
from src.strategies.market_maker import MarketMakerStrategy


class Backtester:
    """
    Backtesting engine for trading strategies
    Replays historical tick data and simulates strategy execution
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 initial_cash: float = 100000.0,
                 transaction_fee_bps: float = 0.0):
        """
        Initialize backtester
        
        Args:
            data: Historical OHLCV data
            initial_cash: Starting cash balance
            transaction_fee_bps: Transaction fees in basis points
        """
        self.data = data.copy()
        self.initial_cash = initial_cash
        self.transaction_fee_bps = transaction_fee_bps
        
        # Prepare data
        self._prepare_data()
        
        # Backtest state
        self.current_idx = 0
        self.is_running = False
        
        # Results storage
        self.equity_curve = []
        self.trades = []
        self.positions = []
        
        print(f"✅ Backtester initialized")
        print(f"   Data points: {len(self.data)}")
        print(f"   Date range: {self.data['timestamp'].min()} to {self.data['timestamp'].max()}")
        print(f"   Initial cash: ${initial_cash:,.2f}")
    
    def _prepare_data(self):
        """Prepare data for backtesting"""
        # Ensure timestamp column
        if 'open_time' in self.data.columns and 'timestamp' not in self.data.columns:
            self.data['timestamp'] = pd.to_datetime(self.data['open_time'])
        
        # Sort by time
        self.data = self.data.sort_values('timestamp').reset_index(drop=True)
        
        # Add mid price if not present
        if 'mid_price' not in self.data.columns:
            self.data['mid_price'] = (self.data['high'] + self.data['low']) / 2
        
        print(f"✅ Data prepared for backtesting")
    
    def run_backtest(self, 
                     strategy_params: Dict,
                     progress_interval: int = 1000) -> Dict:
        """
        Run backtest with market maker strategy
        
        Args:
            strategy_params: Parameters for market maker strategy
            progress_interval: Print progress every N bars
            
        Returns:
            dict: Backtest results
        """
        print("\n" + "="*70)
        print("STARTING BACKTEST")
        print("="*70)
        print(f"Strategy: Market Maker")
        print(f"Parameters: {strategy_params}")
        print(f"Data points: {len(self.data)}")
        
        # Create order book and engine
        orderbook = OrderBook("BTCUSDT")
        engine = MatchingEngine(orderbook, latency_ms=1.0)
        
        # Initialize order book with first prices
        first_row = self.data.iloc[0]
        initial_price = first_row['close']
        
        # Add initial liquidity
        for i in range(5):
            offset = (i + 1) * 20
            engine.submit_limit_order("BUY", initial_price - offset, 1.0, f"INIT_BID_{i}")
            engine.submit_limit_order("SELL", initial_price + offset, 1.0, f"INIT_ASK_{i}")
        
        # Create strategy
        strategy = MarketMakerStrategy(
            orderbook=orderbook,
            matching_engine=engine,
            base_spread_bps=strategy_params.get('base_spread_bps', 10.0),
            order_size=strategy_params.get('order_size', 0.1),
            max_inventory=strategy_params.get('max_inventory', 5.0),
            initial_cash=self.initial_cash
        )
        
        strategy.start()
        
        # Run backtest
        print("\n🚀 Running backtest...")
        start_time = datetime.now()
        
        for idx, row in self.data.iterrows():
            # Create market state
            market_state = {
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'mid_price': row['mid_price'],
                'best_bid': row['close'] - 5,  # Approximate
                'best_ask': row['close'] + 5,
                'spread': 10.0
            }
            
            # Update strategy
            strategy.on_tick(market_state)
            
            # Simulate some random market orders hitting our quotes
            if idx % 10 == 0:  # Every 10 bars
                # Random chance of aggressive order
                if np.random.random() < 0.3:
                    is_buy = np.random.random() < 0.5
                    qty = np.random.uniform(0.05, 0.15)
                    
                    if is_buy and orderbook.best_ask:
                        price = orderbook.best_ask * 1.001
                        engine.submit_limit_order("BUY", price, qty, "TAKER")
                    elif not is_buy and orderbook.best_bid:
                        price = orderbook.best_bid * 0.999
                        engine.submit_limit_order("SELL", price, qty, "TAKER")
                    
                    # Process any trades
                    for trade in orderbook.trades[-5:]:
                        if trade.get('buyer') == 'MarketMaker' or trade.get('seller') == 'MarketMaker':
                            strategy.on_trade(trade)
            
            # Record equity
            current_price = row['close']
            pnl_snapshot = strategy.pnl_tracker.calculate_pnl(current_price)
            
            self.equity_curve.append({
                'timestamp': row['timestamp'],
                'portfolio_value': pnl_snapshot['portfolio_value'],
                'cash': pnl_snapshot['cash'],
                'inventory': pnl_snapshot['inventory'],
                'total_pnl': pnl_snapshot['total_pnl'],
                'price': current_price
            })
            
            # Progress update
            if idx % progress_interval == 0 and idx > 0:
                progress = (idx / len(self.data)) * 100
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"  Progress: {progress:.1f}% | "
                      f"Time: {elapsed:.1f}s | "
                      f"Trades: {strategy.trades_executed} | "
                      f"PnL: ${pnl_snapshot['total_pnl']:.2f}")
        
        strategy.stop()
        
        # Final results
        elapsed_time = (datetime.now() - start_time).total_seconds()
        print(f"\n✅ Backtest completed in {elapsed_time:.1f}s")
        
        final_price = self.data.iloc[-1]['close']
        final_stats = strategy.get_comprehensive_statistics(final_price)
        
        results = {
            'strategy_stats': final_stats,
            'equity_curve': pd.DataFrame(self.equity_curve),
            'trades': strategy.pnl_tracker.trades,
            'execution_time': elapsed_time,
            'data_points': len(self.data),
            'initial_cash': self.initial_cash,
            'final_portfolio_value': final_stats['portfolio_value'],
            'total_return_pct': final_stats['total_return_pct']
        }
        
        return results
    
    def print_backtest_summary(self, results: Dict):
        """Print backtest summary"""
        stats = results['strategy_stats']
        
        print("\n" + "="*70)
        print("BACKTEST SUMMARY")
        print("="*70)
        print(f"Duration: {results['execution_time']:.1f}s")
        print(f"Data Points: {results['data_points']:,}")
        
        print(f"\n💰 Performance:")
        print(f"  Initial Capital: ${results['initial_cash']:,.2f}")
        print(f"  Final Portfolio: ${results['final_portfolio_value']:,.2f}")
        print(f"  Total Return: {results['total_return_pct']:+.2f}%")
        print(f"  Total PnL: ${stats['total_pnl']:,.2f}")
        print(f"  Realized PnL: ${stats['realized_pnl']:,.2f}")
        print(f"  Unrealized PnL: ${stats['unrealized_pnl']:,.2f}")
        
        print(f"\n📈 Trading Activity:")
        print(f"  Total Trades: {stats['trades_executed']}")
        print(f"  Buys: {stats['num_buys']} ({stats['total_buy_volume']:.4f} BTC)")
        print(f"  Sells: {stats['num_sells']} ({stats['total_sell_volume']:.4f} BTC)")
        print(f"  Win Rate: {stats['win_rate_pct']:.1f}%")
        
        print(f"\n⚖️ Risk Management:")
        print(f"  Final Inventory: {stats['inventory']['current_inventory']:.4f} BTC")
        print(f"  Max Inventory: {stats['inventory']['max_inventory_reached']:.4f} BTC")
        print(f"  Inventory Breaches: {stats['inventory']['inventory_breaches']}")
        
        print("="*70)


def test_backtester():
    """Test the backtester with sample data"""
    print("="*70)
    print("BACKTESTER TEST")
    print("="*70)
    
    # Load real data
    from src.data.data_processor import DataProcessor
    
    processor = DataProcessor()
    
    # Try to load the most recent data file
    import os
    from pathlib import Path
    
    data_dir = Path("data/raw")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No data files found! Run data_fetcher.py first.")
        return
    
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"\n📂 Loading data from: {latest_file.name}")
    
    data = processor.load_data(str(latest_file))
    
    # Use first 1000 rows for quick test
    print(f"\n⚡ Using first 1000 rows for quick test...")
    data = data.head(1000)
    
    # Create backtester
    backtester = Backtester(
        data=data,
        initial_cash=100000.0,
        transaction_fee_bps=0.0
    )
    
    # Strategy parameters
    strategy_params = {
        'base_spread_bps': 10.0,
        'order_size': 0.1,
        'max_inventory': 3.0
    }
    
    # Run backtest
    results = backtester.run_backtest(strategy_params, progress_interval=200)
    
    # Print summary
    backtester.print_backtest_summary(results)
    
    print("\n✅ Backtester test completed!")


if __name__ == "__main__":
    test_backtester()