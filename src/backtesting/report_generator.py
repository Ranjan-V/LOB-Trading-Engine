"""
Report Generator
Creates comprehensive backtest reports with visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtesting.performance_analyzer import PerformanceAnalyzer


class ReportGenerator:
    """
    Generates comprehensive backtest reports
    Creates visualizations and exports to HTML/PDF
    """
    
    def __init__(self, backtest_results: dict):
        """
        Initialize report generator
        
        Args:
            backtest_results: Results from backtester
        """
        self.results = backtest_results
        self.equity_curve = backtest_results['equity_curve'].copy()
        self.trades = backtest_results['trades']
        self.stats = backtest_results['strategy_stats']
        
        # Add returns column if missing
        if 'returns' not in self.equity_curve.columns:
            self.equity_curve['returns'] = self.equity_curve['portfolio_value'].pct_change()
        
        # Create analyzer
        self.analyzer = PerformanceAnalyzer(self.equity_curve, self.trades)
        
        # Set plotting style
        sns.set_style("darkgrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
        print(f"✅ ReportGenerator initialized")
    
    def plot_equity_curve(self, save_path: str = None):
        """
        Plot portfolio equity curve
        
        Args:
            save_path: Path to save plot (optional)
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot equity curve
        ax1.plot(self.equity_curve['timestamp'], 
                self.equity_curve['portfolio_value'],
                linewidth=2, color='#2E86AB', label='Portfolio Value')
        
        ax1.axhline(y=self.results['initial_cash'], 
                   color='gray', linestyle='--', alpha=0.5, label='Initial Capital')
        
        ax1.set_title('Portfolio Equity Curve', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Format y-axis as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        # Plot drawdown
        portfolio_values = self.equity_curve['portfolio_value']
        running_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values - running_max) / running_max * 100
        
        ax2.fill_between(self.equity_curve['timestamp'], drawdown, 0, 
                        color='#A23B72', alpha=0.5, label='Drawdown')
        ax2.plot(self.equity_curve['timestamp'], drawdown, 
                color='#A23B72', linewidth=1)
        
        ax2.set_title('Drawdown Over Time', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  💾 Saved equity curve to: {save_path}")
        
        return fig
    
    def plot_returns_distribution(self, save_path: str = None):
        """
        Plot returns distribution
        
        Args:
            save_path: Path to save plot (optional)
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        returns = self.equity_curve['returns'].dropna() * 100
        
        # Histogram
        ax1.hist(returns, bins=50, color='#18A558', alpha=0.7, edgecolor='black')
        ax1.axvline(returns.mean(), color='red', linestyle='--', 
                   linewidth=2, label=f'Mean: {returns.mean():.3f}%')
        ax1.axvline(0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
        
        ax1.set_title('Returns Distribution', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Returns (%)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Q-Q plot (check normality)
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normality Check)', fontsize=16, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  💾 Saved returns distribution to: {save_path}")
        
        return fig
    
    def plot_trade_analysis(self, save_path: str = None):
        """
        Plot trade analysis
        
        Args:
            save_path: Path to save plot (optional)
        """
        if not self.trades:
            print("  ⚠️ No trades to plot")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        trades_df = pd.DataFrame(self.trades)
        
        # Trade PnL
        buy_trades = trades_df[trades_df['side'] == 'BUY']
        sell_trades = trades_df[trades_df['side'] == 'SELL']
        
        ax1.scatter(range(len(buy_trades)), buy_trades['price'], 
                   color='green', marker='^', s=100, alpha=0.6, label='Buy')
        ax1.scatter(range(len(sell_trades)), sell_trades['price'], 
                   color='red', marker='v', s=100, alpha=0.6, label='Sell')
        
        ax1.set_title('Trade Execution Prices', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Trade Number', fontsize=11)
        ax1.set_ylabel('Price ($)', fontsize=11)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Inventory over time
        cumulative_inventory = []
        inventory = 0
        for trade in self.trades:
            if trade['side'] == 'BUY':
                inventory += trade['quantity']
            else:
                inventory -= trade['quantity']
            cumulative_inventory.append(inventory)
        
        ax2.plot(cumulative_inventory, color='#F18F01', linewidth=2)
        ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax2.set_title('Inventory Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Trade Number', fontsize=11)
        ax2.set_ylabel('Inventory (BTC)', fontsize=11)
        ax2.grid(True, alpha=0.3)
        
        # Trade size distribution
        ax3.hist(trades_df['quantity'], bins=30, color='#6A4C93', alpha=0.7, edgecolor='black')
        ax3.set_title('Trade Size Distribution', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Quantity (BTC)', fontsize=11)
        ax3.set_ylabel('Frequency', fontsize=11)
        ax3.grid(True, alpha=0.3)
        
        # Cumulative trades
        ax4.plot(range(len(buy_trades)), np.arange(len(buy_trades)), 
                color='green', label='Buys', linewidth=2)
        ax4.plot(range(len(sell_trades)), np.arange(len(sell_trades)), 
                color='red', label='Sells', linewidth=2)
        ax4.set_title('Cumulative Trades', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Time', fontsize=11)
        ax4.set_ylabel('Cumulative Count', fontsize=11)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  💾 Saved trade analysis to: {save_path}")
        
        return fig
    
    def generate_report(self, output_dir: str = "results/backtest_reports"):
        """
        Generate complete backtest report with all visualizations
        
        Args:
            output_dir: Directory to save report files
        """
        print("\n" + "="*70)
        print("GENERATING BACKTEST REPORT")
        print("="*70)
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate plots
        print("\n📊 Creating visualizations...")
        
        equity_path = output_path / f"equity_curve_{timestamp}.png"
        self.plot_equity_curve(str(equity_path))
        
        returns_path = output_path / f"returns_dist_{timestamp}.png"
        self.plot_returns_distribution(str(returns_path))
        
        trades_path = output_path / f"trade_analysis_{timestamp}.png"
        self.plot_trade_analysis(str(trades_path))
        
        # Print comprehensive metrics
        print("\n📈 Performance Metrics:")
        self.analyzer.print_metrics()
        
        # Save metrics to CSV
        metrics = self.analyzer.get_comprehensive_metrics()
        metrics_df = pd.DataFrame([metrics])
        metrics_path = output_path / f"metrics_{timestamp}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        print(f"\n  💾 Saved metrics to: {metrics_path}")
        
        # Save equity curve
        equity_path_csv = output_path / f"equity_curve_{timestamp}.csv"
        self.equity_curve.to_csv(equity_path_csv, index=False)
        print(f"  💾 Saved equity curve data to: {equity_path_csv}")
        
        print("\n" + "="*70)
        print("✅ REPORT GENERATION COMPLETE")
        print("="*70)
        print(f"\nAll files saved to: {output_path.absolute()}")
        print("\nGenerated files:")
        print(f"  1. Equity curve plot: equity_curve_{timestamp}.png")
        print(f"  2. Returns distribution: returns_dist_{timestamp}.png")
        print(f"  3. Trade analysis: trade_analysis_{timestamp}.png")
        print(f"  4. Performance metrics: metrics_{timestamp}.csv")
        print(f"  5. Equity curve data: equity_curve_{timestamp}.csv")
        print("="*70)


def test_report_generator():
    """Test report generator with real backtest results"""
    print("="*70)
    print("REPORT GENERATOR TEST")
    print("="*70)
    
    # Run a quick backtest
    from src.backtesting.backtester import Backtester
    from src.data.data_processor import DataProcessor
    import os
    
    # Load data
    processor = DataProcessor()
    data_dir = Path("data/raw")
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        print("❌ No data files found!")
        return
    
    latest_file = max(csv_files, key=os.path.getctime)
    data = processor.load_data(str(latest_file))
    
    # Use first 1000 rows
    data = data.head(1000)
    
    # Run backtest
    backtester = Backtester(data=data, initial_cash=100000.0)
    
    strategy_params = {
        'base_spread_bps': 10.0,
        'order_size': 0.1,
        'max_inventory': 3.0
    }
    
    print("\n🚀 Running backtest...")
    results = backtester.run_backtest(strategy_params, progress_interval=500)
    
    # Generate report
    print("\n📊 Generating report...")
    report_gen = ReportGenerator(results)
    report_gen.generate_report()
    
    print("\n✅ Report generator test completed!")
    print("\n💡 Check the 'results/backtest_reports' folder for all generated files!")


if __name__ == "__main__":
    test_report_generator()