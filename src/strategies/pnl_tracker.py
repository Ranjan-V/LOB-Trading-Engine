"""
PnL Tracker Module
Tracks profit and loss for trading strategies
"""

from typing import Dict, List
from datetime import datetime
import numpy as np


class PnLTracker:
    """
    Tracks profit and loss for a trading strategy
    Calculates realized and unrealized PnL
    """
    
    def __init__(self, initial_cash: float = 100000.0, initial_inventory: float = 0.0):
        """
        Initialize PnL tracker
        
        Args:
            initial_cash: Starting cash balance (USD)
            initial_inventory: Starting inventory (BTC)
        """
        self.initial_cash = initial_cash
        self.initial_inventory = initial_inventory
        
        # Current positions
        self.cash = initial_cash
        self.inventory = initial_inventory
        
        # PnL tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.total_pnl = 0.0
        
        # Trade history
        self.trades: List[Dict] = []
        self.pnl_history: List[Dict] = []
        
        # Statistics
        self.total_buy_volume = 0.0
        self.total_sell_volume = 0.0
        self.total_fees = 0.0
        self.num_buys = 0
        self.num_sells = 0
        
        print(f"✅ PnLTracker initialized")
        print(f"   Initial Cash: ${initial_cash:,.2f}")
        print(f"   Initial Inventory: {initial_inventory:.4f} BTC")
    
    def record_buy(self, price: float, quantity: float, fee: float = 0.0):
        """
        Record a buy trade
        
        Args:
            price: Buy price
            quantity: Quantity bought
            fee: Transaction fee
        """
        cost = price * quantity + fee
        
        # Update positions
        self.cash -= cost
        self.inventory += quantity
        
        # Record trade
        trade = {
            'timestamp': datetime.now(),
            'side': 'BUY',
            'price': price,
            'quantity': quantity,
            'cost': cost,
            'fee': fee,
            'cash': self.cash,
            'inventory': self.inventory
        }
        self.trades.append(trade)
        
        # Update statistics
        self.total_buy_volume += quantity
        self.total_fees += fee
        self.num_buys += 1
    
    def record_sell(self, price: float, quantity: float, fee: float = 0.0):
        """
        Record a sell trade
        
        Args:
            price: Sell price
            quantity: Quantity sold
            fee: Transaction fee
        """
        proceeds = price * quantity - fee
        
        # Update positions
        self.cash += proceeds
        self.inventory -= quantity
        
        # Record trade
        trade = {
            'timestamp': datetime.now(),
            'side': 'SELL',
            'price': price,
            'quantity': quantity,
            'proceeds': proceeds,
            'fee': fee,
            'cash': self.cash,
            'inventory': self.inventory
        }
        self.trades.append(trade)
        
        # Update statistics
        self.total_sell_volume += quantity
        self.total_fees += fee
        self.num_sells += 1
    
    def calculate_pnl(self, current_price: float) -> Dict:
        """
        Calculate current PnL
        
        Args:
            current_price: Current market price
            
        Returns:
            dict: PnL breakdown
        """
        # Calculate portfolio value
        portfolio_value = self.cash + (self.inventory * current_price)
        initial_value = self.initial_cash + (self.initial_inventory * current_price)
        
        # Total PnL
        self.total_pnl = portfolio_value - initial_value
        
        # Unrealized PnL (from current inventory)
        if len(self.trades) > 0:
            # Calculate average cost basis
            buy_trades = [t for t in self.trades if t['side'] == 'BUY']
            if buy_trades and self.inventory > 0:
                total_cost = sum(t['price'] * t['quantity'] for t in buy_trades)
                total_qty = sum(t['quantity'] for t in buy_trades)
                avg_cost = total_cost / total_qty if total_qty > 0 else current_price
                
                self.unrealized_pnl = (current_price - avg_cost) * self.inventory
            else:
                self.unrealized_pnl = 0.0
            
            # Realized PnL
            self.realized_pnl = self.total_pnl - self.unrealized_pnl
        else:
            self.unrealized_pnl = 0.0
            self.realized_pnl = self.total_pnl
        
        # Record PnL snapshot
        pnl_snapshot = {
            'timestamp': datetime.now(),
            'current_price': current_price,
            'cash': self.cash,
            'inventory': self.inventory,
            'portfolio_value': portfolio_value,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl
        }
        self.pnl_history.append(pnl_snapshot)
        
        return pnl_snapshot
    
    def get_statistics(self, current_price: float) -> Dict:
        """
        Get comprehensive statistics
        
        Args:
            current_price: Current market price
            
        Returns:
            dict: Statistics
        """
        pnl = self.calculate_pnl(current_price)
        
        # Calculate returns
        initial_value = self.initial_cash + (self.initial_inventory * current_price)
        total_return_pct = (self.total_pnl / initial_value * 100) if initial_value > 0 else 0
        
        # Calculate win rate
        profitable_trades = 0
        if len(self.trades) >= 2:
            for i in range(1, len(self.trades)):
                if self.trades[i]['side'] == 'SELL' and self.trades[i-1]['side'] == 'BUY':
                    if self.trades[i]['price'] > self.trades[i-1]['price']:
                        profitable_trades += 1
        
        num_round_trips = min(self.num_buys, self.num_sells)
        win_rate = (profitable_trades / num_round_trips * 100) if num_round_trips > 0 else 0
        
        return {
            'current_price': current_price,
            'portfolio_value': pnl['portfolio_value'],
            'cash': self.cash,
            'inventory': self.inventory,
            'total_pnl': self.total_pnl,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'total_return_pct': total_return_pct,
            'num_trades': len(self.trades),
            'num_buys': self.num_buys,
            'num_sells': self.num_sells,
            'total_buy_volume': self.total_buy_volume,
            'total_sell_volume': self.total_sell_volume,
            'total_fees': self.total_fees,
            'win_rate_pct': win_rate
        }
    
    def print_statistics(self, current_price: float):
        """Print PnL statistics"""
        stats = self.get_statistics(current_price)
        
        print("\n" + "="*70)
        print("PNL TRACKER STATISTICS")
        print("="*70)
        print(f"Current Price: ${stats['current_price']:,.2f}")
        print(f"\nPortfolio:")
        print(f"  Cash: ${stats['cash']:,.2f}")
        print(f"  Inventory: {stats['inventory']:.4f} BTC")
        print(f"  Portfolio Value: ${stats['portfolio_value']:,.2f}")
        print(f"\nPnL:")
        print(f"  Total: ${stats['total_pnl']:,.2f} ({stats['total_return_pct']:+.2f}%)")
        print(f"  Realized: ${stats['realized_pnl']:,.2f}")
        print(f"  Unrealized: ${stats['unrealized_pnl']:,.2f}")
        print(f"\nTrading Activity:")
        print(f"  Total Trades: {stats['num_trades']}")
        print(f"  Buys: {stats['num_buys']} ({stats['total_buy_volume']:.4f} BTC)")
        print(f"  Sells: {stats['num_sells']} ({stats['total_sell_volume']:.4f} BTC)")
        print(f"  Total Fees: ${stats['total_fees']:,.2f}")
        print(f"  Win Rate: {stats['win_rate_pct']:.1f}%")
        print("="*70)


# Test PnL tracker
if __name__ == "__main__":
    print("="*70)
    print("PNL TRACKER TEST")
    print("="*70)
    
    # Create tracker
    tracker = PnLTracker(initial_cash=100000.0, initial_inventory=0.0)
    
    # Simulate some trades
    print("\n1️⃣ Simulating buy trade...")
    tracker.record_buy(price=50000, quantity=1.0, fee=10)
    
    print("\n2️⃣ Calculating PnL at $50,500...")
    pnl = tracker.calculate_pnl(current_price=50500)
    print(f"   Total PnL: ${pnl['total_pnl']:,.2f}")
    print(f"   Unrealized PnL: ${pnl['unrealized_pnl']:,.2f}")
    
    print("\n3️⃣ Simulating sell trade...")
    tracker.record_sell(price=50500, quantity=0.5, fee=5)
    
    print("\n4️⃣ Final PnL at $51,000...")
    tracker.print_statistics(current_price=51000)
    
    print("\n✅ PnL tracker test completed!")