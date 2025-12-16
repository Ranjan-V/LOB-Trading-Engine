"""
Performance Analyzer
Calculates comprehensive performance metrics for backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class PerformanceAnalyzer:
    """
    Analyzes trading strategy performance
    Calculates: Sharpe ratio, max drawdown, win rate, etc.
    """
    
    def __init__(self, equity_curve: pd.DataFrame, trades: List[Dict], risk_free_rate: float = 0.02):
        """
        Initialize performance analyzer
        
        Args:
            equity_curve: DataFrame with portfolio values over time
            trades: List of executed trades
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.equity_curve = equity_curve.copy()
        self.trades = trades
        self.risk_free_rate = risk_free_rate
        
        # Calculate returns
        self.equity_curve['returns'] = self.equity_curve['portfolio_value'].pct_change()
        self.equity_curve['cumulative_returns'] = (1 + self.equity_curve['returns']).cumprod() - 1
        
        print(f"✅ PerformanceAnalyzer initialized")
        print(f"   Equity curve length: {len(equity_curve)}")
        print(f"   Total trades: {len(trades)}")
    
    def calculate_total_return(self) -> float:
        """Calculate total return percentage"""
        if len(self.equity_curve) == 0:
            return 0.0
        
        initial_value = self.equity_curve['portfolio_value'].iloc[0]
        final_value = self.equity_curve['portfolio_value'].iloc[-1]
        
        return ((final_value - initial_value) / initial_value) * 100
    
    def calculate_cagr(self, years: float = None) -> float:
        """
        Calculate Compound Annual Growth Rate
        
        Args:
            years: Time period in years (auto-calculated if None)
            
        Returns:
            float: CAGR percentage
        """
        if len(self.equity_curve) == 0:
            return 0.0
        
        initial_value = self.equity_curve['portfolio_value'].iloc[0]
        final_value = self.equity_curve['portfolio_value'].iloc[-1]
        
        if years is None:
            # Calculate years from timestamps
            start_date = self.equity_curve['timestamp'].iloc[0]
            end_date = self.equity_curve['timestamp'].iloc[-1]
            years = (end_date - start_date).total_seconds() / (365.25 * 24 * 3600)
        
        if years <= 0:
            return 0.0
        
        cagr = (pow(final_value / initial_value, 1 / years) - 1) * 100
        return cagr
    
    def calculate_sharpe_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe ratio (annualized)
        
        Args:
            periods_per_year: Number of trading periods per year
            
        Returns:
            float: Sharpe ratio
        """
        returns = self.equity_curve['returns'].dropna()
        
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / periods_per_year)
        sharpe = np.sqrt(periods_per_year) * (excess_returns.mean() / returns.std())
        
        return sharpe
    
    def calculate_sortino_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sortino ratio (uses downside deviation)
        
        Args:
            periods_per_year: Number of trading periods per year
            
        Returns:
            float: Sortino ratio
        """
        returns = self.equity_curve['returns'].dropna()
        
        if len(returns) == 0:
            return 0.0
        
        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / periods_per_year)
        sortino = np.sqrt(periods_per_year) * (excess_returns.mean() / downside_returns.std())
        
        return sortino
    
    def calculate_max_drawdown(self) -> Dict:
        """
        Calculate maximum drawdown
        
        Returns:
            dict: Max drawdown info (percentage, duration, etc.)
        """
        portfolio_values = self.equity_curve['portfolio_value']
        
        # Calculate running maximum
        running_max = portfolio_values.expanding().max()
        
        # Calculate drawdown
        drawdown = (portfolio_values - running_max) / running_max * 100
        
        # Find maximum drawdown
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find when drawdown started (last peak before max dd)
        peak_idx = portfolio_values[:max_dd_idx].idxmax()
        
        # Calculate drawdown duration
        if 'timestamp' in self.equity_curve.columns:
            dd_duration = self.equity_curve['timestamp'].iloc[max_dd_idx] - self.equity_curve['timestamp'].iloc[peak_idx]
            dd_duration_days = dd_duration.total_seconds() / (24 * 3600)
        else:
            dd_duration_days = max_dd_idx - peak_idx
        
        return {
            'max_drawdown_pct': max_dd,
            'peak_value': portfolio_values.iloc[peak_idx],
            'trough_value': portfolio_values.iloc[max_dd_idx],
            'peak_date': self.equity_curve['timestamp'].iloc[peak_idx] if 'timestamp' in self.equity_curve.columns else peak_idx,
            'trough_date': self.equity_curve['timestamp'].iloc[max_dd_idx] if 'timestamp' in self.equity_curve.columns else max_dd_idx,
            'duration_days': dd_duration_days
        }
    
    def calculate_win_rate(self) -> Dict:
        """
        Calculate win rate and related metrics
        
        Returns:
            dict: Win rate statistics
        """
        if len(self.trades) < 2:
            return {
                'win_rate_pct': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # Pair up buys and sells
        winning_trades = 0
        losing_trades = 0
        total_wins = 0.0
        total_losses = 0.0
        
        buy_price = None
        
        for trade in self.trades:
            if trade['side'] == 'BUY':
                buy_price = trade['price']
            elif trade['side'] == 'SELL' and buy_price is not None:
                pnl = (trade['price'] - buy_price) * trade['quantity']
                
                if pnl > 0:
                    winning_trades += 1
                    total_wins += pnl
                else:
                    losing_trades += 1
                    total_losses += abs(pnl)
                
                buy_price = None
        
        total_trades = winning_trades + losing_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        avg_win = (total_wins / winning_trades) if winning_trades > 0 else 0.0
        avg_loss = (total_losses / losing_trades) if losing_trades > 0 else 0.0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0.0
        
        return {
            'win_rate_pct': win_rate,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def calculate_volatility(self, annualize: bool = True, periods_per_year: int = 252) -> float:
        """
        Calculate volatility (standard deviation of returns)
        
        Args:
            annualize: Whether to annualize volatility
            periods_per_year: Periods per year for annualization
            
        Returns:
            float: Volatility (percentage)
        """
        returns = self.equity_curve['returns'].dropna()
        
        if len(returns) == 0:
            return 0.0
        
        volatility = returns.std() * 100
        
        if annualize:
            volatility *= np.sqrt(periods_per_year)
        
        return volatility
    
    def get_comprehensive_metrics(self) -> Dict:
        """
        Calculate all performance metrics
        
        Returns:
            dict: Complete performance metrics
        """
        total_return = self.calculate_total_return()
        cagr = self.calculate_cagr()
        sharpe = self.calculate_sharpe_ratio()
        sortino = self.calculate_sortino_ratio()
        max_dd = self.calculate_max_drawdown()
        win_rate_stats = self.calculate_win_rate()
        volatility = self.calculate_volatility()
        
        return {
            'total_return_pct': total_return,
            'cagr_pct': cagr,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown_pct': max_dd['max_drawdown_pct'],
            'max_drawdown_duration_days': max_dd['duration_days'],
            'volatility_pct': volatility,
            'win_rate_pct': win_rate_stats['win_rate_pct'],
            'profit_factor': win_rate_stats['profit_factor'],
            'avg_win': win_rate_stats['avg_win'],
            'avg_loss': win_rate_stats['avg_loss'],
            'winning_trades': win_rate_stats['winning_trades'],
            'losing_trades': win_rate_stats['losing_trades']
        }
    
    def print_metrics(self):
        """Print all performance metrics"""
        metrics = self.get_comprehensive_metrics()
        
        print("\n" + "="*70)
        print("PERFORMANCE METRICS")
        print("="*70)
        
        print(f"\n📊 Returns:")
        print(f"  Total Return: {metrics['total_return_pct']:+.2f}%")
        print(f"  CAGR: {metrics['cagr_pct']:+.2f}%")
        print(f"  Volatility: {metrics['volatility_pct']:.2f}%")
        
        print(f"\n📈 Risk-Adjusted Returns:")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"  Sortino Ratio: {metrics['sortino_ratio']:.3f}")
        
        print(f"\n📉 Drawdown:")
        print(f"  Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"  Drawdown Duration: {metrics['max_drawdown_duration_days']:.1f} days")
        
        print(f"\n🎯 Trade Statistics:")
        print(f"  Win Rate: {metrics['win_rate_pct']:.1f}%")
        print(f"  Winning Trades: {metrics['winning_trades']}")
        print(f"  Losing Trades: {metrics['losing_trades']}")
        print(f"  Avg Win: ${metrics['avg_win']:.2f}")
        print(f"  Avg Loss: ${metrics['avg_loss']:.2f}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        
        print("="*70)
        
        # Interpretation
        print(f"\n💡 Interpretation:")
        if metrics['sharpe_ratio'] > 2:
            print("  ✅ Excellent Sharpe ratio (>2.0)")
        elif metrics['sharpe_ratio'] > 1:
            print("  ✅ Good Sharpe ratio (>1.0)")
        else:
            print("  ⚠️  Low Sharpe ratio (<1.0)")
        
        if metrics['max_drawdown_pct'] > -20:
            print("  ✅ Low maximum drawdown (<20%)")
        else:
            print("  ⚠️  High maximum drawdown (>20%)")
        
        if metrics['win_rate_pct'] > 50:
            print("  ✅ Positive win rate (>50%)")
        else:
            print("  ℹ️  Market makers often have <50% win rate but positive expectancy")


# Test performance analyzer
if __name__ == "__main__":
    print("="*70)
    print("PERFORMANCE ANALYZER TEST")
    print("="*70)
    
    # Create sample equity curve
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    
    # Simulate returns with some volatility
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 100)
    portfolio_values = 100000 * (1 + returns).cumprod()
    
    equity_curve = pd.DataFrame({
        'timestamp': dates,
        'portfolio_value': portfolio_values
    })
    
    # Sample trades
    trades = [
        {'side': 'BUY', 'price': 50000, 'quantity': 0.1},
        {'side': 'SELL', 'price': 50500, 'quantity': 0.1},
        {'side': 'BUY', 'price': 50200, 'quantity': 0.1},
        {'side': 'SELL', 'price': 50100, 'quantity': 0.1},
    ]
    
    # Create analyzer
    analyzer = PerformanceAnalyzer(equity_curve, trades)
    
    # Print metrics
    analyzer.print_metrics()
    
    print("\n✅ Performance analyzer test completed!")