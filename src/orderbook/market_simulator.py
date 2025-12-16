"""
Market Simulator Module
Simulates realistic market activity using Poisson-based order flow
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orderbook.orderbook import OrderBook
from src.orderbook.matching_engine import MatchingEngine
from src.orderbook.order import create_limit_order


class MarketSimulator:
    """
    Simulates realistic market order flow
    - Poisson arrival process for orders
    - Realistic price/size distributions
    - Market maker and taker behavior
    """
    
    def __init__(self, 
                 symbol: str = "BTCUSDT",
                 initial_price: float = 50000.0,
                 lambda_arrival: float = 1.0,  # orders per second
                 spread_bps: float = 10.0):     # spread in basis points
        """
        Initialize market simulator
        
        Args:
            symbol: Trading symbol
            initial_price: Starting mid price
            lambda_arrival: Poisson lambda (orders per second)
            spread_bps: Initial spread in basis points (1 bps = 0.01%)
        """
        self.symbol = symbol
        self.current_price = initial_price
        self.lambda_arrival = lambda_arrival
        self.spread_bps = spread_bps
        
        # Create order book and matching engine
        self.orderbook = OrderBook(symbol)
        self.engine = MatchingEngine(self.orderbook, latency_ms=1.0)
        
        # Simulation parameters
        self.trader_counter = 0
        self.simulation_time = 0.0  # seconds
        
        # Order flow statistics
        self.order_history = []
        self.price_history = []
        
        print(f"✅ MarketSimulator initialized")
        print(f"   Symbol: {symbol}")
        print(f"   Initial Price: ${initial_price:,.2f}")
        print(f"   Order Arrival Rate: {lambda_arrival} orders/sec")
        print(f"   Initial Spread: {spread_bps} bps")
    
    def initialize_book(self, num_levels: int = 10, liquidity_per_level: float = 1.0):
        """
        Initialize order book with liquidity on both sides
        
        Args:
            num_levels: Number of price levels on each side
            liquidity_per_level: Quantity at each level
        """
        print(f"\n📊 Initializing order book with {num_levels} levels...")
        
        spread = self.current_price * (self.spread_bps / 10000)
        bid_price = self.current_price - spread / 2
        ask_price = self.current_price + spread / 2
        
        tick_size = spread / 2  # Price increment between levels
        
        # Add buy orders (market makers)
        for i in range(num_levels):
            price = bid_price - (i * tick_size)
            quantity = liquidity_per_level * (1 + np.random.uniform(-0.2, 0.2))
            self.engine.submit_limit_order("BUY", price, quantity, f"MM_BID_{i}")
        
        # Add sell orders (market makers)
        for i in range(num_levels):
            price = ask_price + (i * tick_size)
            quantity = liquidity_per_level * (1 + np.random.uniform(-0.2, 0.2))
            self.engine.submit_limit_order("SELL", price, quantity, f"MM_ASK_{i}")
        
        print(f"✅ Order book initialized")
        self.orderbook.print_book(levels=5)
    
    def generate_order(self) -> Dict:
        """
        Generate a random order based on realistic distributions
        
        Returns:
            dict: Order parameters
        """
        # Determine order side (50/50 buy/sell)
        side = "BUY" if np.random.random() < 0.5 else "SELL"
        
        # Determine if aggressive (market taker) or passive (market maker)
        is_aggressive = np.random.random() < 0.3  # 30% aggressive
        
        # Get current best prices
        best_bid = self.orderbook.best_bid or self.current_price
        best_ask = self.orderbook.best_ask or self.current_price
        mid_price = (best_bid + best_ask) / 2
        
        # Generate order size (log-normal distribution)
        base_size = 0.1
        size = np.random.lognormal(mean=np.log(base_size), sigma=0.5)
        size = max(0.01, min(size, 5.0))  # Clip to reasonable range
        
        # Determine price based on aggressiveness
        if is_aggressive:
            # Aggressive orders: cross the spread
            if side == "BUY":
                price = best_ask * (1 + np.random.uniform(0, 0.001))
            else:
                price = best_bid * (1 - np.random.uniform(0, 0.001))
        else:
            # Passive orders: add liquidity
            tick_size = mid_price * 0.0001  # 1 bps
            if side == "BUY":
                # Place below best bid
                offset = np.random.randint(0, 5) * tick_size
                price = best_bid - offset
            else:
                # Place above best ask
                offset = np.random.randint(0, 5) * tick_size
                price = best_ask + offset
        
        return {
            'side': side,
            'price': round(price, 2),
            'quantity': round(size, 4),
            'is_aggressive': is_aggressive
        }
    
    def simulate_step(self) -> Optional[Dict]:
        """
        Simulate one time step
        
        Returns:
            dict: Order execution report (if order generated)
        """
        # Check if order arrives (Poisson process)
        dt = 0.1  # Time step in seconds
        arrival_probability = 1 - np.exp(-self.lambda_arrival * dt)
        
        if np.random.random() < arrival_probability:
            # Generate and submit order
            order_params = self.generate_order()
            
            self.trader_counter += 1
            trader_id = f"TRADER_{self.trader_counter}"
            
            report = self.engine.submit_limit_order(
                side=order_params['side'],
                price=order_params['price'],
                quantity=order_params['quantity'],
                trader_id=trader_id
            )
            
            # Record order
            self.order_history.append({
                'time': self.simulation_time,
                'side': order_params['side'],
                'price': order_params['price'],
                'quantity': order_params['quantity'],
                'is_aggressive': order_params['is_aggressive'],
                'filled': report['filled_quantity']
            })
            
            # Update price if trade occurred
            if report['avg_price']:
                self.current_price = report['avg_price']
            
            return report
        
        self.simulation_time += dt
        return None
    
    def simulate(self, duration_seconds: float, verbose: bool = False) -> pd.DataFrame:
        """
        Run market simulation
        
        Args:
            duration_seconds: How long to simulate
            verbose: Print progress
            
        Returns:
            pd.DataFrame: Simulation results
        """
        print(f"\n🚀 Starting simulation for {duration_seconds} seconds...")
        
        num_steps = int(duration_seconds / 0.1)
        
        for step in range(num_steps):
            report = self.simulate_step()
            
            # Record price every step
            mid_price = self.orderbook.mid_price or self.current_price
            self.price_history.append({
                'time': self.simulation_time,
                'mid_price': mid_price,
                'best_bid': self.orderbook.best_bid,
                'best_ask': self.orderbook.best_ask,
                'spread': self.orderbook.spread
            })
            
            if verbose and step % 100 == 0:
                progress = (step / num_steps) * 100
                print(f"  Progress: {progress:.1f}% | Time: {self.simulation_time:.1f}s | "
                      f"Mid: ${mid_price:.2f} | Orders: {len(self.order_history)}")
        
        print(f"\n✅ Simulation completed!")
        print(f"   Total time: {self.simulation_time:.1f}s")
        print(f"   Orders generated: {len(self.order_history)}")
        print(f"   Final mid price: ${self.orderbook.mid_price:.2f}")
        
        # Convert to DataFrame
        price_df = pd.DataFrame(self.price_history)
        return price_df
    
    def get_simulation_summary(self) -> Dict:
        """Get summary statistics of simulation"""
        if not self.price_history:
            return {}
        
        price_df = pd.DataFrame(self.price_history)
        order_df = pd.DataFrame(self.order_history)
        
        summary = {
            'total_orders': len(self.order_history),
            'total_trades': self.engine.total_trades,
            'total_volume': self.engine.total_volume,
            'avg_spread': price_df['spread'].mean() if 'spread' in price_df else None,
            'price_volatility': price_df['mid_price'].std(),
            'final_price': price_df['mid_price'].iloc[-1],
            'price_change': price_df['mid_price'].iloc[-1] - price_df['mid_price'].iloc[0],
            'aggressive_orders': order_df['is_aggressive'].sum() if len(order_df) > 0 else 0
        }
        
        return summary
    
    def print_summary(self):
        """Print simulation summary"""
        summary = self.get_simulation_summary()
        
        print("\n" + "="*70)
        print("MARKET SIMULATION SUMMARY")
        print("="*70)
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total Volume: {summary['total_volume']:.4f}")
        print(f"Aggressive Orders: {summary['aggressive_orders']}")
        print(f"\nPrice Statistics:")
        print(f"  Final Price: ${summary['final_price']:,.2f}")
        print(f"  Price Change: ${summary['price_change']:,.2f}")
        print(f"  Volatility: ${summary['price_volatility']:.2f}")
        print(f"  Avg Spread: ${summary['avg_spread']:.2f}")
        print("="*70)


def test_market_simulator():
    """Test the market simulator"""
    print("="*70)
    print("MARKET SIMULATOR TEST")
    print("="*70)
    
    # Create simulator
    sim = MarketSimulator(
        symbol="BTCUSDT",
        initial_price=50000.0,
        lambda_arrival=2.0,  # 2 orders per second
        spread_bps=10.0
    )
    
    # Initialize order book
    sim.initialize_book(num_levels=10, liquidity_per_level=0.5)
    
    # Run simulation
    price_df = sim.simulate(duration_seconds=30.0, verbose=True)
    
    # Print final book state
    sim.orderbook.print_book()
    
    # Print summary
    sim.print_summary()
    
    print("\n✅ Market simulator test completed!")
    print(f"\n💾 Price data shape: {price_df.shape}")
    print(f"   Columns: {price_df.columns.tolist()}")


if __name__ == "__main__":
    test_market_simulator()