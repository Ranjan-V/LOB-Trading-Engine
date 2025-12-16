"""
Market Maker Strategy
Complete market making strategy with inventory management and PnL tracking
"""

import numpy as np
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.base_strategy import BaseStrategy
from src.strategies.inventory_manager import InventoryManager
from src.strategies.pnl_tracker import PnLTracker
from src.orderbook.orderbook import OrderBook
from src.orderbook.matching_engine import MatchingEngine
from src.orderbook.order import Order, create_limit_order


class MarketMakerStrategy(BaseStrategy):
    """
    Market making strategy that:
    - Quotes bid/ask spreads continuously
    - Manages inventory risk
    - Tracks PnL in real-time
    - Adjusts quotes based on market conditions
    """
    
    def __init__(self,
                 orderbook: OrderBook,
                 matching_engine: MatchingEngine,
                 base_spread_bps: float = 10.0,
                 order_size: float = 0.1,
                 max_inventory: float = 5.0,
                 initial_cash: float = 100000.0):
        """
        Initialize market maker strategy
        
        Args:
            orderbook: OrderBook instance
            matching_engine: MatchingEngine instance
            base_spread_bps: Base spread in basis points (1 bps = 0.01%)
            order_size: Order size for quotes
            max_inventory: Maximum inventory limit
            initial_cash: Initial cash balance
        """
        super().__init__("MarketMaker", orderbook, matching_engine)
        
        # Strategy parameters
        self.base_spread_bps = base_spread_bps
        self.base_order_size = order_size
        
        # Initialize inventory manager
        self.inventory_manager = InventoryManager(
            target_inventory=0.0,
            max_inventory=max_inventory,
            inventory_risk_aversion=0.01
        )
        
        # Initialize PnL tracker
        self.pnl_tracker = PnLTracker(
            initial_cash=initial_cash,
            initial_inventory=0.0
        )
        
        # Active quotes
        self.active_bid_order = None
        self.active_ask_order = None
        
        # Performance metrics
        self.quote_updates = 0
        self.trades_executed = 0
        
        print(f"\n📊 Market Maker Parameters:")
        print(f"   Base Spread: {base_spread_bps} bps")
        print(f"   Order Size: {order_size} BTC")
        print(f"   Max Inventory: ±{max_inventory} BTC")
    
    def on_tick(self, market_data: Dict) -> List[Order]:
        """
        Called on every market tick
        Updates quotes based on current market state
        
        Args:
            market_data: Current market state
            
        Returns:
            list: Orders to submit (not used in this implementation)
        """
        if not self.is_running:
            return []
        
        # Get current market state
        mid_price = market_data.get('mid_price')
        if not mid_price:
            return []
        
        # Calculate base spread in dollars
        base_spread = mid_price * (self.base_spread_bps / 10000)
        
        # Get optimal quotes from inventory manager
        optimal_quotes = self.inventory_manager.calculate_optimal_quotes(
            mid_price, base_spread
        )
        
        # Calculate quote sizes
        bid_size = self.inventory_manager.get_quote_size("BUY", self.base_order_size)
        ask_size = self.inventory_manager.get_quote_size("SELL", self.base_order_size)
        
        # Cancel existing quotes
        self._cancel_active_quotes()
        
        # Place new quotes
        if bid_size > 0 and self.inventory_manager.should_quote("BUY"):
            self._place_bid(optimal_quotes['bid_price'], bid_size)
        
        if ask_size > 0 and self.inventory_manager.should_quote("SELL"):
            self._place_ask(optimal_quotes['ask_price'], ask_size)
        
        self.quote_updates += 1
        
        # Update PnL
        self.pnl_tracker.calculate_pnl(mid_price)
        
        return []
    
    def _place_bid(self, price: float, size: float):
        """Place bid order"""
        report = self.submit_order("BUY", price, size)
        if report:
            self.active_bid_order = {
                'order_id': report['order_id'],
                'price': price,
                'size': size
            }
    
    def _place_ask(self, price: float, size: float):
        """Place ask order"""
        report = self.submit_order("SELL", price, size)
        if report:
            self.active_ask_order = {
                'order_id': report['order_id'],
                'price': price,
                'size': size
            }
    
    def _cancel_active_quotes(self):
        """Cancel existing active quotes"""
        if self.active_bid_order:
            self.cancel_order(self.active_bid_order['order_id'])
            self.active_bid_order = None
        
        if self.active_ask_order:
            self.cancel_order(self.active_ask_order['order_id'])
            self.active_ask_order = None
    
    def on_trade(self, trade: Dict):
        """
        Called when a trade occurs
        Updates inventory and PnL
        
        Args:
            trade: Trade information
        """
        # Record trade in PnL tracker
        if trade['buyer'] == self.strategy_name:
            self.pnl_tracker.record_buy(
                price=trade['price'],
                quantity=trade['quantity'],
                fee=0.0  # No fees in simulation
            )
            self.inventory_manager.update_inventory(
                quantity=trade['quantity'],
                price=trade['price']
            )
            self.trades_executed += 1
        
        elif trade['seller'] == self.strategy_name:
            self.pnl_tracker.record_sell(
                price=trade['price'],
                quantity=trade['quantity'],
                fee=0.0
            )
            self.inventory_manager.update_inventory(
                quantity=-trade['quantity'],
                price=trade['price']
            )
            self.trades_executed += 1
    
    def on_order_filled(self, order: Order, fill_price: float, fill_quantity: float):
        """
        Called when an order is filled
        
        Args:
            order: The filled order
            fill_price: Execution price
            fill_quantity: Filled quantity
        """
        self.num_trades += 1
    
    def get_comprehensive_statistics(self, current_price: float) -> Dict:
        """
        Get comprehensive strategy statistics
        
        Args:
            current_price: Current market price
            
        Returns:
            dict: Complete statistics
        """
        base_stats = self.get_statistics()
        pnl_stats = self.pnl_tracker.get_statistics(current_price)
        inventory_metrics = self.inventory_manager.get_inventory_metrics()
        
        return {
            **base_stats,
            **pnl_stats,
            'inventory': inventory_metrics,
            'quote_updates': self.quote_updates,
            'trades_executed': self.trades_executed
        }
    
    def print_comprehensive_statistics(self, current_price: float):
        """Print detailed strategy statistics"""
        stats = self.get_comprehensive_statistics(current_price)
        
        print("\n" + "="*70)
        print("MARKET MAKER STRATEGY - COMPREHENSIVE STATISTICS")
        print("="*70)
        
        print(f"\n💼 Strategy Status:")
        print(f"   Status: {'🟢 Running' if stats['is_running'] else '🔴 Stopped'}")
        print(f"   Quote Updates: {stats['quote_updates']}")
        print(f"   Trades Executed: {stats['trades_executed']}")
        
        print(f"\n📊 Portfolio:")
        print(f"   Cash: ${stats['cash']:,.2f}")
        print(f"   Inventory: {stats['inventory']['current_inventory']:.4f} BTC")
        print(f"   Inventory %: {stats['inventory']['inventory_pct']:.1f}%")
        print(f"   Portfolio Value: ${stats['portfolio_value']:,.2f}")
        
        print(f"\n💰 PnL:")
        print(f"   Total: ${stats['total_pnl']:,.2f} ({stats['total_return_pct']:+.2f}%)")
        print(f"   Realized: ${stats['realized_pnl']:,.2f}")
        print(f"   Unrealized: ${stats['unrealized_pnl']:,.2f}")
        
        print(f"\n📈 Trading Activity:")
        print(f"   Total Trades: {stats['num_trades']}")
        print(f"   Buys: {stats['num_buys']} ({stats['total_buy_volume']:.4f} BTC)")
        print(f"   Sells: {stats['num_sells']} ({stats['total_sell_volume']:.4f} BTC)")
        print(f"   Win Rate: {stats['win_rate_pct']:.1f}%")
        
        print(f"\n⚖️ Risk Management:")
        print(f"   Inventory Skew: {stats['inventory']['skew']:.4f}")
        print(f"   Neutral: {'✅' if stats['inventory']['is_neutral'] else '❌'}")
        print(f"   Max Inventory: {stats['inventory']['max_inventory_reached']:.4f}")
        print(f"   Breaches: {stats['inventory']['inventory_breaches']}")
        
        print("="*70)


def test_market_maker():
    """Test the market maker strategy with live simulation"""
    from src.orderbook.market_simulator import MarketSimulator
    
    print("="*70)
    print("MARKET MAKER STRATEGY TEST")
    print("="*70)
    
    # Create market simulator
    simulator = MarketSimulator(
        symbol="BTCUSDT",
        initial_price=50000.0,
        lambda_arrival=1.0,
        spread_bps=10.0
    )
    
    # Initialize order book
    simulator.initialize_book(num_levels=10, liquidity_per_level=1.0)
    
    # Create market maker strategy
    mm_strategy = MarketMakerStrategy(
        orderbook=simulator.orderbook,
        matching_engine=simulator.engine,
        base_spread_bps=10.0,
        order_size=0.2,
        max_inventory=3.0,
        initial_cash=100000.0
    )
    
    # Start strategy
    mm_strategy.start()
    
    # Run simulation with market maker
    print("\n🚀 Running simulation with market maker for 60 seconds...")
    
    num_ticks = 600  # 60 seconds at 0.1s per tick
    
    for tick in range(num_ticks):
        # Get market state
        market_state = mm_strategy.get_market_state()
        
        # Update market maker quotes
        mm_strategy.on_tick(market_state)
        
        # Simulate one market step
        simulator.simulate_step()
        
        # Check for trades involving our strategy
        recent_trades = simulator.orderbook.trades[-10:]  # Last 10 trades
        for trade in recent_trades:
            if (trade.get('buyer') == 'MarketMaker' or 
                trade.get('seller') == 'MarketMaker'):
                mm_strategy.on_trade(trade)
        
        # Print progress
        if tick % 100 == 0 and tick > 0:
            progress = (tick / num_ticks) * 100
            mid_price = market_state.get('mid_price', 50000)
            print(f"  Progress: {progress:.0f}% | "
                  f"Mid: ${mid_price:.2f} | "
                  f"MM Trades: {mm_strategy.trades_executed}")
    
    # Stop strategy
    mm_strategy.stop()
    
    # Print final statistics
    final_price = simulator.orderbook.mid_price or 50000
    mm_strategy.print_comprehensive_statistics(final_price)
    
    # Print order book state
    simulator.orderbook.print_book()
    
    print("\n✅ Market maker test completed!")


if __name__ == "__main__":
    test_market_maker()