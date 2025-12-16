"""
Inventory Manager Module
Manages inventory risk for market making strategies
"""

import numpy as np
from typing import Dict, Optional


class InventoryManager:
    """
    Manages inventory risk and calculates optimal quotes
    Uses inventory skewing to manage risk exposure
    """
    
    def __init__(self,
                 target_inventory: float = 0.0,
                 max_inventory: float = 10.0,
                 inventory_risk_aversion: float = 0.01):
        """
        Initialize inventory manager
        
        Args:
            target_inventory: Target inventory level (neutral = 0)
            max_inventory: Maximum allowed inventory
            inventory_risk_aversion: Risk aversion parameter (higher = more conservative)
        """
        self.target_inventory = target_inventory
        self.max_inventory = max_inventory
        self.inventory_risk_aversion = inventory_risk_aversion
        
        # Current state
        self.current_inventory = target_inventory
        self.inventory_value = 0.0
        
        # Risk metrics
        self.max_inventory_reached = 0.0
        self.inventory_breaches = 0
        
        print(f"✅ InventoryManager initialized")
        print(f"   Target Inventory: {target_inventory:.4f}")
        print(f"   Max Inventory: ±{max_inventory:.4f}")
        print(f"   Risk Aversion: {inventory_risk_aversion}")
    
    def update_inventory(self, quantity: float, price: float):
        """
        Update inventory position
        
        Args:
            quantity: Change in inventory (positive = buy, negative = sell)
            price: Transaction price
        """
        self.current_inventory += quantity
        self.inventory_value = self.current_inventory * price
        
        # Track max inventory
        abs_inventory = abs(self.current_inventory)
        if abs_inventory > self.max_inventory_reached:
            self.max_inventory_reached = abs_inventory
        
        # Check for breaches
        if abs_inventory > self.max_inventory:
            self.inventory_breaches += 1
    
    def get_inventory_skew(self) -> float:
        """
        Calculate inventory skew based on current position
        Positive skew = need to sell (widen ask, tighten bid)
        Negative skew = need to buy (widen bid, tighten ask)
        
        Returns:
            float: Skew adjustment in basis points
        """
        # Calculate deviation from target
        deviation = self.current_inventory - self.target_inventory
        
        # Skew increases as inventory moves away from target
        skew = deviation * self.inventory_risk_aversion
        
        return skew
    
    def calculate_quote_adjustment(self, base_spread: float) -> Dict[str, float]:
        """
        Calculate bid/ask price adjustments based on inventory
        
        Args:
            base_spread: Base spread to use
            
        Returns:
            dict: Bid and ask adjustments
        """
        skew = self.get_inventory_skew()
        
        # If inventory is too high (long), widen ask and tighten bid
        # If inventory is too low (short), widen bid and tighten ask
        
        bid_adjustment = -skew  # Negative skew when long -> tighten bid
        ask_adjustment = skew   # Positive skew when long -> widen ask
        
        return {
            'bid_adjustment': bid_adjustment,
            'ask_adjustment': ask_adjustment,
            'skew': skew
        }
    
    def calculate_optimal_quotes(self, 
                                 mid_price: float,
                                 base_spread: float) -> Dict[str, float]:
        """
        Calculate optimal bid and ask prices
        
        Args:
            mid_price: Current mid price
            base_spread: Base spread in dollars
            
        Returns:
            dict: Optimal bid and ask prices
        """
        adjustments = self.calculate_quote_adjustment(base_spread)
        
        half_spread = base_spread / 2
        
        # Apply inventory adjustments
        bid_price = mid_price - half_spread + adjustments['bid_adjustment']
        ask_price = mid_price + half_spread + adjustments['ask_adjustment']
        
        return {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'spread': ask_price - bid_price,
            'skew': adjustments['skew']
        }
    
    def should_quote(self, side: str) -> bool:
        """
        Determine if we should quote on a given side
        
        Args:
            side: 'BUY' or 'SELL'
            
        Returns:
            bool: Whether to quote on this side
        """
        # Don't quote if at max inventory
        if side.upper() == "BUY" and self.current_inventory >= self.max_inventory:
            return False
        
        if side.upper() == "SELL" and self.current_inventory <= -self.max_inventory:
            return False
        
        return True
    
    def get_quote_size(self, side: str, base_size: float) -> float:
        """
        Calculate quote size based on inventory
        Reduce size as inventory moves away from target
        
        Args:
            side: 'BUY' or 'SELL'
            base_size: Base order size
            
        Returns:
            float: Adjusted order size
        """
        if not self.should_quote(side):
            return 0.0
        
        # Calculate inventory utilization
        inventory_pct = abs(self.current_inventory) / self.max_inventory
        
        # Reduce size as inventory increases
        size_multiplier = max(0.1, 1.0 - inventory_pct * 0.5)
        
        # Further reduce if quoting in direction that increases inventory
        if side.upper() == "BUY" and self.current_inventory > self.target_inventory:
            size_multiplier *= 0.5
        elif side.upper() == "SELL" and self.current_inventory < self.target_inventory:
            size_multiplier *= 0.5
        
        return base_size * size_multiplier
    
    def is_inventory_neutral(self, threshold: float = 0.1) -> bool:
        """
        Check if inventory is close to neutral
        
        Args:
            threshold: Threshold for neutrality
            
        Returns:
            bool: True if inventory is neutral
        """
        deviation = abs(self.current_inventory - self.target_inventory)
        return deviation < threshold
    
    def get_inventory_metrics(self) -> Dict:
        """
        Get inventory metrics
        
        Returns:
            dict: Inventory statistics
        """
        inventory_pct = (self.current_inventory / self.max_inventory * 100) if self.max_inventory > 0 else 0
        
        return {
            'current_inventory': self.current_inventory,
            'target_inventory': self.target_inventory,
            'max_inventory': self.max_inventory,
            'inventory_pct': inventory_pct,
            'inventory_value': self.inventory_value,
            'is_neutral': self.is_inventory_neutral(),
            'skew': self.get_inventory_skew(),
            'max_inventory_reached': self.max_inventory_reached,
            'inventory_breaches': self.inventory_breaches
        }
    
    def print_metrics(self):
        """Print inventory metrics"""
        metrics = self.get_inventory_metrics()
        
        print("\n" + "="*70)
        print("INVENTORY MANAGER METRICS")
        print("="*70)
        print(f"Current Inventory: {metrics['current_inventory']:.4f} BTC")
        print(f"Target Inventory: {metrics['target_inventory']:.4f} BTC")
        print(f"Max Inventory: ±{metrics['max_inventory']:.4f} BTC")
        print(f"Inventory %: {metrics['inventory_pct']:.1f}%")
        print(f"Inventory Value: ${metrics['inventory_value']:,.2f}")
        print(f"Neutral: {'✅' if metrics['is_neutral'] else '❌'}")
        print(f"Skew: {metrics['skew']:.4f}")
        print(f"Max Reached: {metrics['max_inventory_reached']:.4f}")
        print(f"Breaches: {metrics['inventory_breaches']}")
        print("="*70)


# Test inventory manager
if __name__ == "__main__":
    print("="*70)
    print("INVENTORY MANAGER TEST")
    print("="*70)
    
    # Create manager
    manager = InventoryManager(
        target_inventory=0.0,
        max_inventory=5.0,
        inventory_risk_aversion=0.01
    )
    
    mid_price = 50000.0
    base_spread = 50.0
    
    # Test neutral inventory
    print("\n1️⃣ Testing with neutral inventory (0.0)...")
    quotes = manager.calculate_optimal_quotes(mid_price, base_spread)
    print(f"   Bid: ${quotes['bid_price']:,.2f}")
    print(f"   Ask: ${quotes['ask_price']:,.2f}")
    print(f"   Spread: ${quotes['spread']:.2f}")
    print(f"   Skew: {quotes['skew']:.4f}")
    
    # Simulate buying (increase inventory)
    print("\n2️⃣ Simulating buy of 2.0 BTC...")
    manager.update_inventory(2.0, mid_price)
    manager.print_metrics()
    
    # Recalculate quotes with long inventory
    print("\n3️⃣ Recalculating quotes with long inventory...")
    quotes = manager.calculate_optimal_quotes(mid_price, base_spread)
    print(f"   Bid: ${quotes['bid_price']:,.2f} (tighter)")
    print(f"   Ask: ${quotes['ask_price']:,.2f} (wider)")
    print(f"   Spread: ${quotes['spread']:.2f}")
    print(f"   Skew: {quotes['skew']:.4f}")
    
    # Test quote sizes
    print("\n4️⃣ Testing quote sizes...")
    buy_size = manager.get_quote_size("BUY", 1.0)
    sell_size = manager.get_quote_size("SELL", 1.0)
    print(f"   Buy size: {buy_size:.4f} (reduced due to long position)")
    print(f"   Sell size: {sell_size:.4f} (normal)")
    
    # Simulate selling back to neutral
    print("\n5️⃣ Selling back to neutral...")
    manager.update_inventory(-2.0, mid_price + 100)
    manager.print_metrics()
    
    print("\n✅ Inventory manager test completed!")