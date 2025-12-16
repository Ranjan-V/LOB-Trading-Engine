"""
Matching Engine Module
Advanced order matching with market impact and latency simulation
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orderbook.orderbook import OrderBook
from src.orderbook.order import Order, create_limit_order, create_market_order


class MatchingEngine:
    """
    Advanced matching engine with realistic market mechanics
    - Simulates latency
    - Calculates market impact
    - Tracks slippage
    - Handles market orders intelligently
    """
    
    def __init__(self, orderbook: OrderBook, latency_ms: float = 1.0):
        """
        Initialize matching engine
        
        Args:
            orderbook: OrderBook instance
            latency_ms: Simulated latency in milliseconds
        """
        self.orderbook = orderbook
        self.latency_ms = latency_ms
        
        # Statistics
        self.total_trades = 0
        self.total_volume = 0.0
        self.total_slippage = 0.0
        
        print(f"✅ MatchingEngine initialized (latency={latency_ms}ms)")
    
    def submit_order(self, order: Order) -> Dict:
        """
        Submit order with latency simulation
        
        Args:
            order: Order to submit
            
        Returns:
            dict: Execution report
        """
        # Simulate network latency
        submission_time = datetime.now()
        arrival_time = submission_time + timedelta(milliseconds=self.latency_ms)
        
        # Add to order book and match
        trades = self.orderbook.add_order(order)
        
        # Calculate execution statistics
        execution_report = self._create_execution_report(
            order, trades, submission_time, arrival_time
        )
        
        return execution_report
    
    def submit_limit_order(self, side: str, price: float, quantity: float,
                          trader_id: str = "TRADER") -> Dict:
        """
        Submit limit order
        
        Args:
            side: 'BUY' or 'SELL'
            price: Limit price
            quantity: Order size
            trader_id: Trader ID
            
        Returns:
            dict: Execution report
        """
        order = create_limit_order(side, price, quantity, trader_id)
        return self.submit_order(order)
    
    def submit_market_order(self, side: str, quantity: float,
                           trader_id: str = "TRADER") -> Dict:
        """
        Submit market order
        
        Args:
            side: 'BUY' or 'SELL'
            quantity: Order size
            trader_id: Trader ID
            
        Returns:
            dict: Execution report
        """
        # For market orders, set price very high (buy) or very low (sell)
        # to ensure they match
        price = 1e9 if side.upper() == "BUY" else 0.01
        order = create_limit_order(side, price, quantity, trader_id)
        
        return self.submit_order(order)
    
    def _create_execution_report(self, order: Order, trades: List[dict],
                                submission_time: datetime,
                                arrival_time: datetime) -> Dict:
        """
        Create detailed execution report
        
        Args:
            order: Original order
            trades: List of executed trades
            submission_time: When order was submitted
            arrival_time: When order arrived at exchange
            
        Returns:
            dict: Execution report with statistics
        """
        if not trades:
            # Order not executed
            return {
                'order_id': order.order_id,
                'status': order.status.value,
                'filled_quantity': 0.0,
                'remaining_quantity': order.quantity,
                'avg_price': None,
                'slippage': 0.0,
                'num_trades': 0,
                'latency_ms': self.latency_ms,
                'trades': []
            }
        
        # Calculate execution statistics
        total_filled = sum(t['quantity'] for t in trades)
        weighted_price = sum(t['price'] * t['quantity'] for t in trades) / total_filled
        
        # Calculate slippage (difference from mid price at submission)
        reference_price = self.orderbook.mid_price or weighted_price
        slippage = abs(weighted_price - reference_price) / reference_price * 100
        
        self.total_slippage += slippage
        self.total_trades += len(trades)
        self.total_volume += total_filled
        
        return {
            'order_id': order.order_id,
            'status': order.status.value,
            'filled_quantity': order.filled_quantity,
            'remaining_quantity': order.remaining_quantity,
            'avg_price': weighted_price,
            'slippage_pct': slippage,
            'num_trades': len(trades),
            'latency_ms': self.latency_ms,
            'trades': trades
        }
    
    def calculate_market_impact(self, side: str, quantity: float) -> Dict:
        """
        Estimate market impact of a large order
        
        Args:
            side: 'BUY' or 'SELL'
            quantity: Order size
            
        Returns:
            dict: Impact analysis
        """
        bids, asks = self.orderbook.get_book_depth(levels=20)
        
        if side.upper() == "BUY":
            # Walk through ask side
            available_liquidity = asks
            reference_price = self.orderbook.best_ask
        else:
            # Walk through bid side
            available_liquidity = bids
            reference_price = self.orderbook.best_bid
        
        if not reference_price:
            return {
                'error': 'No liquidity available',
                'impact_pct': None,
                'avg_price': None
            }
        
        # Calculate how much we can fill and at what price
        remaining = quantity
        total_cost = 0.0
        levels_consumed = 0
        
        for price, qty in available_liquidity:
            if remaining <= 0:
                break
            
            fillable = min(remaining, qty)
            total_cost += price * fillable
            remaining -= fillable
            levels_consumed += 1
        
        if remaining > 0:
            # Not enough liquidity
            return {
                'error': f'Insufficient liquidity (need {remaining:.4f} more)',
                'impact_pct': None,
                'avg_price': None,
                'levels_consumed': levels_consumed
            }
        
        avg_execution_price = total_cost / quantity
        impact_pct = abs(avg_execution_price - reference_price) / reference_price * 100
        
        return {
            'quantity': quantity,
            'avg_price': avg_execution_price,
            'reference_price': reference_price,
            'impact_pct': impact_pct,
            'levels_consumed': levels_consumed,
            'total_cost': total_cost
        }
    
    def get_statistics(self) -> Dict:
        """Get matching engine statistics"""
        avg_slippage = self.total_slippage / max(self.total_trades, 1)
        
        return {
            'total_trades': self.total_trades,
            'total_volume': self.total_volume,
            'avg_slippage_pct': avg_slippage,
            'latency_ms': self.latency_ms
        }
    
    def print_statistics(self):
        """Print matching engine statistics"""
        stats = self.get_statistics()
        
        print("\n" + "="*70)
        print("MATCHING ENGINE STATISTICS")
        print("="*70)
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Total Volume: {stats['total_volume']:.4f}")
        print(f"Avg Slippage: {stats['avg_slippage_pct']:.4f}%")
        print(f"Latency: {stats['latency_ms']:.2f}ms")
        print("="*70)


def test_matching_engine():
    """Test the matching engine"""
    print("="*70)
    print("MATCHING ENGINE TEST")
    print("="*70)
    
    # Create order book and matching engine
    book = OrderBook("BTCUSDT")
    engine = MatchingEngine(book, latency_ms=2.0)
    
    # Add initial liquidity
    print("\n1️⃣ Adding initial liquidity...")
    engine.submit_limit_order("BUY", 50000, 2.0, "MM_1")
    engine.submit_limit_order("BUY", 49950, 1.5, "MM_2")
    engine.submit_limit_order("BUY", 49900, 3.0, "MM_3")
    
    engine.submit_limit_order("SELL", 50050, 1.8, "MM_4")
    engine.submit_limit_order("SELL", 50100, 2.2, "MM_5")
    engine.submit_limit_order("SELL", 50150, 2.5, "MM_6")
    
    book.print_book()
    
    # Test market impact calculation
    print("\n2️⃣ Testing market impact calculation...")
    impact = engine.calculate_market_impact("BUY", 3.0)
    print(f"\nImpact of buying 3.0 BTC:")
    print(f"  Average price: ${impact['avg_price']:,.2f}")
    print(f"  Reference price: ${impact['reference_price']:,.2f}")
    print(f"  Market impact: {impact['impact_pct']:.2f}%")
    print(f"  Levels consumed: {impact['levels_consumed']}")
    
    # Execute a large order
    print("\n3️⃣ Executing large buy order...")
    report = engine.submit_limit_order("BUY", 50120, 2.5, "TRADER_1")
    
    print(f"\nExecution Report:")
    print(f"  Order ID: {report['order_id'][:8]}...")
    print(f"  Status: {report['status']}")
    print(f"  Filled: {report['filled_quantity']:.4f}")
    print(f"  Avg Price: ${report['avg_price']:,.2f}")
    print(f"  Slippage: {report['slippage_pct']:.4f}%")
    print(f"  Num Trades: {report['num_trades']}")
    
    book.print_book()
    
    # Engine statistics
    engine.print_statistics()
    
    print("\n✅ Matching engine test completed!")


if __name__ == "__main__":
    test_matching_engine()