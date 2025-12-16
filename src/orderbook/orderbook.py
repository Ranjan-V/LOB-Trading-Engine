"""
Order Book Module
Implements a limit order book with price-time priority
"""

from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.orderbook.order import Order, OrderSide, OrderType, OrderStatus


class PriceLevel:
    """
    Represents all orders at a specific price level
    Uses FIFO (first-in-first-out) for price-time priority
    """
    
    def __init__(self, price: float):
        self.price = price
        self.orders = deque()  # FIFO queue of orders
        self.total_quantity = 0.0
    
    def add_order(self, order: Order):
        """Add order to this price level"""
        self.orders.append(order)
        self.total_quantity += order.remaining_quantity
    
    def remove_order(self, order: Order) -> bool:
        """Remove order from this price level"""
        try:
            self.orders.remove(order)
            self.total_quantity -= order.remaining_quantity
            return True
        except ValueError:
            return False
    
    def is_empty(self) -> bool:
        """Check if price level has no orders"""
        return len(self.orders) == 0
    
    def __repr__(self) -> str:
        return f"PriceLevel(${self.price:.2f}, qty={self.total_quantity:.4f}, orders={len(self.orders)})"


class OrderBook:
    """
    Limit Order Book with price-time priority matching
    
    Maintains separate bid (buy) and ask (sell) sides
    """
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        
        # Price levels: price -> PriceLevel
        self.bids: Dict[float, PriceLevel] = {}  # Buy orders (descending price)
        self.asks: Dict[float, PriceLevel] = {}  # Sell orders (ascending price)
        
        # Order tracking: order_id -> Order
        self.orders: Dict[str, Order] = {}
        
        # Trade history
        self.trades: List[dict] = []
        
        # Statistics
        self.total_volume = 0.0
        self.num_trades = 0
        
        print(f"✅ OrderBook initialized for {symbol}")
    
    def add_order(self, order: Order) -> List[dict]:
        """
        Add order to the book and attempt to match
        
        Args:
            order: Order to add
            
        Returns:
            list: List of trades executed
        """
        # Try to match the order first
        trades = self._match_order(order)
        
        # If order is not completely filled, add to book
        if not order.is_filled:
            self._add_to_book(order)
            self.orders[order.order_id] = order
        
        return trades
    
    def _add_to_book(self, order: Order):
        """Add unfilled order to the book"""
        if order.side == OrderSide.BUY:
            if order.price not in self.bids:
                self.bids[order.price] = PriceLevel(order.price)
            self.bids[order.price].add_order(order)
        else:
            if order.price not in self.asks:
                self.asks[order.price] = PriceLevel(order.price)
            self.asks[order.price].add_order(order)
    
    def _match_order(self, order: Order) -> List[dict]:
        """
        Match incoming order against existing orders
        
        Args:
            order: Incoming order to match
            
        Returns:
            list: List of executed trades
        """
        trades = []
        
        if order.side == OrderSide.BUY:
            # Match against asks (sell orders)
            trades = self._match_buy_order(order)
        else:
            # Match against bids (buy orders)
            trades = self._match_sell_order(order)
        
        return trades
    
    def _match_buy_order(self, buy_order: Order) -> List[dict]:
        """Match buy order against sell orders"""
        trades = []
        
        # Get sorted ask prices (lowest first)
        sorted_ask_prices = sorted(self.asks.keys())
        
        for ask_price in sorted_ask_prices:
            # Stop if buy price is lower than ask price (no match possible)
            if buy_order.order_type == OrderType.LIMIT and buy_order.price < ask_price:
                break
            
            # Stop if buy order is filled
            if buy_order.is_filled:
                break
            
            price_level = self.asks[ask_price]
            
            # Match against orders at this price level (FIFO)
            while price_level.orders and not buy_order.is_filled:
                sell_order = price_level.orders[0]
                
                # Calculate trade quantity
                trade_qty = min(buy_order.remaining_quantity, 
                              sell_order.remaining_quantity)
                
                # Execute trade at the ask price (price of resting order)
                trade = self._execute_trade(buy_order, sell_order, ask_price, trade_qty)
                trades.append(trade)
                
                # Remove filled sell order
                if sell_order.is_filled:
                    price_level.orders.popleft()
                    price_level.total_quantity -= sell_order.quantity
                    del self.orders[sell_order.order_id]
            
            # Remove empty price level
            if price_level.is_empty():
                del self.asks[ask_price]
        
        return trades
    
    def _match_sell_order(self, sell_order: Order) -> List[dict]:
        """Match sell order against buy orders"""
        trades = []
        
        # Get sorted bid prices (highest first)
        sorted_bid_prices = sorted(self.bids.keys(), reverse=True)
        
        for bid_price in sorted_bid_prices:
            # Stop if sell price is higher than bid price
            if sell_order.order_type == OrderType.LIMIT and sell_order.price > bid_price:
                break
            
            # Stop if sell order is filled
            if sell_order.is_filled:
                break
            
            price_level = self.bids[bid_price]
            
            # Match against orders at this price level (FIFO)
            while price_level.orders and not sell_order.is_filled:
                buy_order = price_level.orders[0]
                
                # Calculate trade quantity
                trade_qty = min(sell_order.remaining_quantity,
                              buy_order.remaining_quantity)
                
                # Execute trade at the bid price
                trade = self._execute_trade(buy_order, sell_order, bid_price, trade_qty)
                trades.append(trade)
                
                # Remove filled buy order
                if buy_order.is_filled:
                    price_level.orders.popleft()
                    price_level.total_quantity -= buy_order.quantity
                    del self.orders[buy_order.order_id]
            
            # Remove empty price level
            if price_level.is_empty():
                del self.bids[bid_price]
        
        return trades
    
    def _execute_trade(self, buy_order: Order, sell_order: Order, 
                       price: float, quantity: float) -> dict:
        """
        Execute a trade between two orders
        
        Args:
            buy_order: Buy order
            sell_order: Sell order
            price: Execution price
            quantity: Trade quantity
            
        Returns:
            dict: Trade information
        """
        # Fill both orders
        buy_order.fill(quantity, price)
        sell_order.fill(quantity, price)
        
        # Create trade record
        trade = {
            'price': price,
            'quantity': quantity,
            'buy_order_id': buy_order.order_id,
            'sell_order_id': sell_order.order_id,
            'buyer': buy_order.trader_id,
            'seller': sell_order.trader_id,
            'timestamp': buy_order.timestamp
        }
        
        # Update statistics
        self.trades.append(trade)
        self.total_volume += quantity
        self.num_trades += 1
        
        return trade
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        # Remove from book
        if order.side == OrderSide.BUY:
            if order.price in self.bids:
                self.bids[order.price].remove_order(order)
                if self.bids[order.price].is_empty():
                    del self.bids[order.price]
        else:
            if order.price in self.asks:
                self.asks[order.price].remove_order(order)
                if self.asks[order.price].is_empty():
                    del self.asks[order.price]
        
        # Update order status
        order.cancel()
        del self.orders[order_id]
        
        return True
    
    @property
    def best_bid(self) -> Optional[float]:
        """Get highest bid price"""
        return max(self.bids.keys()) if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        """Get lowest ask price"""
        return min(self.asks.keys()) if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        """Get bid-ask spread"""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def mid_price(self) -> Optional[float]:
        """Get mid price"""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None
    
    def get_book_depth(self, levels: int = 10) -> Tuple[List[tuple], List[tuple]]:
        """
        Get order book depth
        
        Args:
            levels: Number of price levels to return
            
        Returns:
            tuple: (bids, asks) where each is [(price, quantity), ...]
        """
        # Bids (descending price)
        bid_prices = sorted(self.bids.keys(), reverse=True)[:levels]
        bids = [(price, self.bids[price].total_quantity) for price in bid_prices]
        
        # Asks (ascending price)
        ask_prices = sorted(self.asks.keys())[:levels]
        asks = [(price, self.asks[price].total_quantity) for price in ask_prices]
        
        return bids, asks
    
    def print_book(self, levels: int = 5):
        """Print order book state"""
        bids, asks = self.get_book_depth(levels)
        
        print("\n" + "="*70)
        print(f"ORDER BOOK: {self.symbol}")
        print("="*70)
        
        print("\n📕 ASKS (Sell Orders)")
        print("-" * 50)
        for price, qty in reversed(asks):
            print(f"  ${price:>10,.2f}  |  {qty:>10.4f}")
        
        print("-" * 50)
        if self.spread:
            print(f"  SPREAD: ${self.spread:.2f} | MID: ${self.mid_price:.2f}")
        print("-" * 50)
        
        print("\n📗 BIDS (Buy Orders)")
        print("-" * 50)
        for price, qty in bids:
            print(f"  ${price:>10,.2f}  |  {qty:>10.4f}")
        print("-" * 50)
        
        print(f"\nTrades: {self.num_trades} | Volume: {self.total_volume:.4f}")
        print("="*70)


# Test the order book
if __name__ == "__main__":
    from src.orderbook.order import create_limit_order
    
    print("="*70)
    print("ORDER BOOK TEST")
    print("="*70)
    
    # Create order book
    book = OrderBook("BTCUSDT")
    
    # Add some orders
    print("\n1️⃣ Adding buy orders...")
    book.add_order(create_limit_order("BUY", 50000, 1.0, "BUYER_1"))
    book.add_order(create_limit_order("BUY", 49900, 0.5, "BUYER_2"))
    book.add_order(create_limit_order("BUY", 49800, 2.0, "BUYER_3"))
    
    print("\n2️⃣ Adding sell orders...")
    book.add_order(create_limit_order("SELL", 50100, 0.8, "SELLER_1"))
    book.add_order(create_limit_order("SELL", 50200, 1.5, "SELLER_2"))
    book.add_order(create_limit_order("SELL", 50300, 1.0, "SELLER_3"))
    
    # Print book state
    book.print_book()
    
    # Add marketable order (will match)
    print("\n3️⃣ Adding marketable buy order (will trade)...")
    trades = book.add_order(create_limit_order("BUY", 50150, 1.0, "BUYER_4"))
    
    print(f"\n✅ Executed {len(trades)} trade(s):")
    for trade in trades:
        print(f"   {trade['quantity']:.4f} @ ${trade['price']:.2f}")
    
    # Print updated book
    book.print_book()
    
    print("\n✅ Order book test completed!")