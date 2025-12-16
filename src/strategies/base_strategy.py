"""
Base Strategy Module
Abstract base class for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orderbook.orderbook import OrderBook
from src.orderbook.matching_engine import MatchingEngine
from src.orderbook.order import Order


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies
    All strategies must implement on_tick() and on_trade()
    """
    
    def __init__(self, 
                 strategy_name: str,
                 orderbook: OrderBook,
                 matching_engine: MatchingEngine):
        """
        Initialize base strategy
        
        Args:
            strategy_name: Name of the strategy
            orderbook: OrderBook instance
            matching_engine: MatchingEngine instance
        """
        self.strategy_name = strategy_name
        self.orderbook = orderbook
        self.matching_engine = matching_engine
        
        # Strategy state
        self.is_running = False
        self.active_orders: Dict[str, Order] = {}  # order_id -> Order
        
        # Performance tracking
        self.total_pnl = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.num_trades = 0
        
        # Event history
        self.trade_history: List[dict] = []
        self.order_history: List[dict] = []
        
        print(f"✅ {strategy_name} initialized")
    
    @abstractmethod
    def on_tick(self, market_data: Dict) -> List[Order]:
        """
        Called on every market tick
        Strategy should decide what orders to place
        
        Args:
            market_data: Current market state
            
        Returns:
            list: Orders to submit
        """
        pass
    
    @abstractmethod
    def on_trade(self, trade: Dict):
        """
        Called when a trade occurs
        
        Args:
            trade: Trade information
        """
        pass
    
    @abstractmethod
    def on_order_filled(self, order: Order, fill_price: float, fill_quantity: float):
        """
        Called when an order is filled
        
        Args:
            order: The filled order
            fill_price: Price at which order was filled
            fill_quantity: Quantity filled
        """
        pass
    
    def start(self):
        """Start the strategy"""
        self.is_running = True
        print(f"🚀 {self.strategy_name} started")
    
    def stop(self):
        """Stop the strategy"""
        self.is_running = False
        self.cancel_all_orders()
        print(f"🛑 {self.strategy_name} stopped")
    
    def submit_order(self, side: str, price: float, quantity: float) -> Optional[Dict]:
        """
        Submit an order through the matching engine
        
        Args:
            side: 'BUY' or 'SELL'
            price: Limit price
            quantity: Order size
            
        Returns:
            dict: Execution report
        """
        if not self.is_running:
            return None
        
        trader_id = f"{self.strategy_name}"
        report = self.matching_engine.submit_limit_order(
            side, price, quantity, trader_id
        )
        
        # Track order
        self.order_history.append({
            'timestamp': datetime.now(),
            'side': side,
            'price': price,
            'quantity': quantity,
            'report': report
        })
        
        return report
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            bool: Success
        """
        success = self.orderbook.cancel_order(order_id)
        
        if success and order_id in self.active_orders:
            del self.active_orders[order_id]
        
        return success
    
    def cancel_all_orders(self):
        """Cancel all active orders"""
        order_ids = list(self.active_orders.keys())
        
        for order_id in order_ids:
            self.cancel_order(order_id)
        
        print(f"  Cancelled {len(order_ids)} orders")
    
    def get_market_state(self) -> Dict:
        """
        Get current market state
        
        Returns:
            dict: Market information
        """
        bids, asks = self.orderbook.get_book_depth(levels=10)
        
        return {
            'best_bid': self.orderbook.best_bid,
            'best_ask': self.orderbook.best_ask,
            'mid_price': self.orderbook.mid_price,
            'spread': self.orderbook.spread,
            'bids': bids,
            'asks': asks,
            'timestamp': datetime.now()
        }
    
    def update_pnl(self, realized: float = 0.0, unrealized: float = 0.0):
        """
        Update PnL tracking
        
        Args:
            realized: Realized PnL from closed trades
            unrealized: Unrealized PnL from open positions
        """
        self.realized_pnl += realized
        self.unrealized_pnl = unrealized
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
    
    def get_statistics(self) -> Dict:
        """
        Get strategy performance statistics
        
        Returns:
            dict: Performance metrics
        """
        return {
            'strategy_name': self.strategy_name,
            'is_running': self.is_running,
            'num_trades': self.num_trades,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'active_orders': len(self.active_orders),
            'total_orders': len(self.order_history)
        }
    
    def print_statistics(self):
        """Print strategy statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print(f"STRATEGY STATISTICS: {stats['strategy_name']}")
        print("="*70)
        print(f"Status: {'🟢 Running' if stats['is_running'] else '🔴 Stopped'}")
        print(f"Total Orders: {stats['total_orders']}")
        print(f"Active Orders: {stats['active_orders']}")
        print(f"Num Trades: {stats['num_trades']}")
        print(f"\nPnL:")
        print(f"  Realized: ${stats['realized_pnl']:,.2f}")
        print(f"  Unrealized: ${stats['unrealized_pnl']:,.2f}")
        print(f"  Total: ${stats['total_pnl']:,.2f}")
        print("="*70)


# Test base strategy
if __name__ == "__main__":
    print("="*70)
    print("BASE STRATEGY MODULE TEST")
    print("="*70)
    print("\n✅ Base strategy class loaded successfully!")
    print("   This is an abstract class - use MarketMaker for implementation")
    print("="*70)