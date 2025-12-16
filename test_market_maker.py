"""
Comprehensive Market Maker Test
Tests market maker with balanced order flow
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.orderbook.orderbook import OrderBook
from src.orderbook.matching_engine import MatchingEngine
from src.strategies.market_maker import MarketMakerStrategy
from src.orderbook.order import create_limit_order
import numpy as np


def run_balanced_test():
    """Run market maker with balanced simulated order flow"""
    
    print("="*70)
    print("MARKET MAKER - BALANCED TEST")
    print("="*70)
    
    # Create order book and engine
    orderbook = OrderBook("BTCUSDT")
    engine = MatchingEngine(orderbook, latency_ms=1.0)
    
    # Initialize with liquidity
    print("\n📊 Initializing order book...")
    initial_price = 50000.0
    
    # Add initial liquidity (other market makers)
    for i in range(5):
        offset = (i + 1) * 10
        engine.submit_limit_order("BUY", initial_price - offset, 0.5, f"OTHER_MM_{i}")
        engine.submit_limit_order("SELL", initial_price + offset, 0.5, f"OTHER_MM_{i+10}")
    
    orderbook.print_book()
    
    # Create our market maker
    print("\n🤖 Creating market maker strategy...")
    mm_strategy = MarketMakerStrategy(
        orderbook=orderbook,
        matching_engine=engine,
        base_spread_bps=8.0,      # 8 bps spread
        order_size=0.1,            # Small size
        max_inventory=2.0,         # 2 BTC max
        initial_cash=50000.0       # $50k starting capital
    )
    
    # Start strategy
    mm_strategy.start()
    
    # Run simulation
    print("\n🚀 Running 30-second simulation with balanced flow...")
    print("   (Simulating aggressive traders hitting both sides)")
    
    num_ticks = 300  # 30 seconds
    start_time = time.time()
    
    for tick in range(num_ticks):
        # Update market maker quotes
        market_state = mm_strategy.get_market_state()
        mm_strategy.on_tick(market_state)
        
        # Simulate random aggressive orders (balanced)
        if tick % 10 == 0:  # Every 1 second
            # 50/50 chance of buy or sell aggressor
            is_buy = np.random.random() < 0.5
            
            if is_buy:
                # Aggressive buyer - will hit market maker's ask
                best_ask = orderbook.best_ask
                if best_ask:
                    qty = np.random.uniform(0.05, 0.15)
                    aggressive_price = best_ask * 1.001  # Cross spread
                    report = engine.submit_limit_order(
                        "BUY", aggressive_price, qty, f"AGGRESSOR_BUY_{tick}"
                    )
                    
                    # Process trades
                    for trade in orderbook.trades[-5:]:
                        if trade.get('seller') == 'MarketMaker':
                            mm_strategy.on_trade(trade)
            else:
                # Aggressive seller - will hit market maker's bid
                best_bid = orderbook.best_bid
                if best_bid:
                    qty = np.random.uniform(0.05, 0.15)
                    aggressive_price = best_bid * 0.999  # Cross spread
                    report = engine.submit_limit_order(
                        "SELL", aggressive_price, qty, f"AGGRESSOR_SELL_{tick}"
                    )
                    
                    # Process trades
                    for trade in orderbook.trades[-5:]:
                        if trade.get('buyer') == 'MarketMaker':
                            mm_strategy.on_trade(trade)
        
        # Progress update
        if tick % 50 == 0 and tick > 0:
            elapsed = time.time() - start_time
            progress = (tick / num_ticks) * 100
            mid = orderbook.mid_price or initial_price
            print(f"  [{elapsed:.1f}s] Progress: {progress:.0f}% | "
                  f"Mid: ${mid:.2f} | "
                  f"Trades: {mm_strategy.trades_executed} | "
                  f"Inventory: {mm_strategy.inventory_manager.current_inventory:.2f}")
    
    # Stop strategy
    mm_strategy.stop()
    
    # Final statistics
    elapsed_time = time.time() - start_time
    print(f"\n✅ Simulation completed in {elapsed_time:.1f}s")
    
    final_price = orderbook.mid_price or initial_price
    mm_strategy.print_comprehensive_statistics(final_price)
    
    # Print final book
    orderbook.print_book()
    
    # Summary
    stats = mm_strategy.get_comprehensive_statistics(final_price)
    
    print("\n" + "="*70)
    print("SIMULATION SUMMARY")
    print("="*70)
    print(f"Duration: {elapsed_time:.1f}s")
    print(f"Market Maker Trades: {stats['trades_executed']}")
    print(f"Total PnL: ${stats['total_pnl']:,.2f}")
    print(f"Return: {stats['total_return_pct']:+.2f}%")
    print(f"Buys: {stats['num_buys']} | Sells: {stats['num_sells']}")
    print(f"Final Inventory: {stats['inventory']['current_inventory']:.4f} BTC")
    print(f"Inventory Neutral: {'✅ Yes' if stats['inventory']['is_neutral'] else '❌ No'}")
    
    if stats['total_pnl'] > 0:
        print(f"\n🎉 PROFITABLE! Market maker earned ${stats['total_pnl']:.2f}")
    else:
        print(f"\n📊 Loss: ${stats['total_pnl']:.2f} (normal in short simulation)")
    
    print("="*70)


if __name__ == "__main__":
    run_balanced_test()