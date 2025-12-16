"""
Order Module
Defines order types and properties for the limit order book
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid


class OrderSide(Enum):
    """Order side - Buy or Sell"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type - Limit or Market"""
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    """
    Represents a single order in the order book
    
    Attributes:
        order_id: Unique order identifier
        side: BUY or SELL
        order_type: LIMIT or MARKET
        price: Limit price (None for market orders)
        quantity: Order size
        timestamp: When order was created
        trader_id: Who placed the order
        status: Current order status
        filled_quantity: How much has been filled
    """
    
    order_id: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    timestamp: datetime
    trader_id: str = "TRADER_DEFAULT"
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    
    def __post_init__(self):
        """Validate order after initialization"""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        
        if self.order_type == OrderType.LIMIT and self.price <= 0:
            raise ValueError("Limit order price must be positive")
    
    @property
    def remaining_quantity(self) -> float:
        """Calculate remaining unfilled quantity"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order"""
        return self.side == OrderSide.BUY
    
    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order"""
        return self.side == OrderSide.SELL
    
    def fill(self, quantity: float, price: float = None) -> float:
        """
        Fill part or all of the order
        
        Args:
            quantity: Amount to fill
            price: Execution price (if different from order price)
            
        Returns:
            float: Amount actually filled
        """
        if quantity <= 0:
            return 0.0
        
        # Calculate how much can be filled
        fillable = min(quantity, self.remaining_quantity)
        
        # Update filled quantity
        self.filled_quantity += fillable
        
        # Update status
        if self.is_filled:
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL
        
        return fillable
    
    def cancel(self):
        """Cancel the order"""
        if self.status not in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            self.status = OrderStatus.CANCELLED
    
    def __repr__(self) -> str:
        """String representation of order"""
        return (f"Order(id={self.order_id[:8]}, {self.side.value} "
                f"{self.quantity:.4f} @ ${self.price:.2f}, "
                f"filled={self.filled_quantity:.4f}, status={self.status.value})")
    
    def to_dict(self) -> dict:
        """Convert order to dictionary"""
        return {
            'order_id': self.order_id,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'price': self.price,
            'quantity': self.quantity,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'timestamp': self.timestamp.isoformat(),
            'trader_id': self.trader_id,
            'status': self.status.value
        }


def create_limit_order(side: str, price: float, quantity: float, 
                       trader_id: str = "TRADER_DEFAULT") -> Order:
    """
    Helper function to create a limit order
    
    Args:
        side: 'BUY' or 'SELL'
        price: Limit price
        quantity: Order size
        trader_id: Trader identifier
        
    Returns:
        Order: Created limit order
    """
    order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
    
    return Order(
        order_id=str(uuid.uuid4()),
        side=order_side,
        order_type=OrderType.LIMIT,
        price=price,
        quantity=quantity,
        timestamp=datetime.now(),
        trader_id=trader_id
    )


def create_market_order(side: str, quantity: float, 
                        trader_id: str = "TRADER_DEFAULT") -> Order:
    """
    Helper function to create a market order
    
    Args:
        side: 'BUY' or 'SELL'
        quantity: Order size
        trader_id: Trader identifier
        
    Returns:
        Order: Created market order
    """
    order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
    
    return Order(
        order_id=str(uuid.uuid4()),
        side=order_side,
        order_type=OrderType.MARKET,
        price=0.0,  # Market orders don't have price
        quantity=quantity,
        timestamp=datetime.now(),
        trader_id=trader_id
    )


# Test the order module
if __name__ == "__main__":
    print("="*70)
    print("ORDER MODULE TEST")
    print("="*70)
    
    # Create buy order
    buy_order = create_limit_order("BUY", 50000.0, 0.5, "TRADER_001")
    print(f"\n✅ Created: {buy_order}")
    
    # Create sell order
    sell_order = create_limit_order("SELL", 50100.0, 0.3, "TRADER_002")
    print(f"✅ Created: {sell_order}")
    
    # Fill part of the order
    filled = buy_order.fill(0.2)
    print(f"\n✅ Filled {filled} BTC")
    print(f"   Order status: {buy_order}")
    print(f"   Remaining: {buy_order.remaining_quantity} BTC")
    
    # Fill rest of order
    filled = buy_order.fill(0.3)
    print(f"\n✅ Filled {filled} BTC")
    print(f"   Order status: {buy_order}")
    print(f"   Is filled: {buy_order.is_filled}")
    
    # Create market order
    market_order = create_market_order("BUY", 1.0, "TRADER_003")
    print(f"\n✅ Created: {market_order}")
    
    print("\n" + "="*70)
    print("✅ Order module test completed!")
    print("="*70)