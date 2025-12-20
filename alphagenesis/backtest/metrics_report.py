"""
Metrics Report Generator

Generates detailed PDF/HTML reports with plots for backtest results.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available, some visualizations will be limited")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available, falling back to Plotly")


class MetricsReportGenerator:
    """
    Generate comprehensive performance reports with visualizations.
    
    Creates:
    - HTML reports with interactive charts
    - PDF reports (if dependencies available)
    - CSV data exports
    - Performance visualizations
    """
    
    def __init__(self, output_dir: str = './reports'):
        """
        Initialize MetricsReportGenerator.
        
        Args:
            output_dir: Directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MetricsReportGenerator initialized, output: {output_dir}")
    
    def generate_full_report(
        self,
        equity_curve: pd.DataFrame,
        trades: pd.DataFrame,
        metrics: Dict[str, Any],
        strategy_name: str = "AlphaGenesis",
    ) -> str:
        """
        Generate comprehensive HTML report.
        
        Args:
            equity_curve: DataFrame with equity history
            trades: DataFrame with trade history
            metrics: Dictionary with performance metrics
            strategy_name: Name of the strategy
            
        Returns:
            Path to generated HTML report
        """
        logger.info(f"Generating full report for {strategy_name}...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f"{strategy_name}_{timestamp}.html"
        
        # Create HTML content
        html_content = self._create_html_report(
            equity_curve, trades, metrics, strategy_name
        )
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Report saved to {report_path}")
        
        return str(report_path)
    
    def _create_html_report(
        self,
        equity_curve: pd.DataFrame,
        trades: pd.DataFrame,
        metrics: Dict[str, Any],
        strategy_name: str,
    ) -> str:
        """Create HTML report content."""
        
        # Generate all visualizations
        equity_chart = self._create_equity_chart(equity_curve)
        drawdown_chart = self._create_drawdown_chart(equity_curve)
        returns_dist = self._create_returns_distribution(trades)
        monthly_returns = self._create_monthly_returns_heatmap(equity_curve)
        
        # Create HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{strategy_name} Performance Report</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .chart-container {{
            margin: 30px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
        }}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>📊 {strategy_name} Performance Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>📈 Key Performance Metrics</h2>
        <div class="metrics-grid">
            {self._format_metrics_cards(metrics)}
        </div>
        
        <h2>💰 Equity Curve</h2>
        <div class="chart-container">
            {equity_chart}
        </div>
        
        <h2>📉 Drawdown Analysis</h2>
        <div class="chart-container">
            {drawdown_chart}
        </div>
        
        <h2>📊 Returns Distribution</h2>
        <div class="chart-container">
            {returns_dist}
        </div>
        
        <h2>📅 Monthly Returns</h2>
        <div class="chart-container">
            {monthly_returns}
        </div>
        
        <h2>🔍 Detailed Metrics</h2>
        {self._format_metrics_table(metrics)}
        
        <h2>📋 Recent Trades</h2>
        {self._format_trades_table(trades)}
        
        <div class="footer">
            <p>AlphaGenesis - AI Trading System for WEEX AI Wars Hackathon</p>
            <p>⚠️ Past performance is not indicative of future results</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _format_metrics_cards(self, metrics: Dict[str, Any]) -> str:
        """Format metrics as HTML cards."""
        cards = []
        
        # Key metrics to display
        key_metrics = [
            ('Total Return', f"{metrics.get('total_return', 0) * 100:.2f}%", 
             'total_return'),
            ('Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}", 
             'sharpe_ratio'),
            ('Max Drawdown', f"{metrics.get('max_drawdown', 0) * 100:.2f}%", 
             'max_drawdown'),
            ('Win Rate', f"{metrics.get('win_rate', 0) * 100:.1f}%", 
             'win_rate'),
            ('Profit Factor', f"{metrics.get('profit_factor', 0):.2f}", 
             'profit_factor'),
            ('Total Trades', f"{metrics.get('num_trades', 0)}", 
             'num_trades'),
        ]
        
        for label, value, key in key_metrics:
            # Determine color based on metric
            if key in ['max_drawdown']:
                value_class = 'negative' if float(value.strip('%')) > 0 else 'positive'
            elif key in ['total_return', 'sharpe_ratio', 'win_rate', 'profit_factor']:
                value_class = 'positive' if float(value.strip('%')) > 0 else 'negative'
            else:
                value_class = ''
            
            card = f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value {value_class}">{value}</div>
            </div>
            """
            cards.append(card)
        
        return ''.join(cards)
    
    def _format_metrics_table(self, metrics: Dict[str, Any]) -> str:
        """Format all metrics as an HTML table."""
        rows = []
        
        for key, value in sorted(metrics.items()):
            # Format value based on type
            if isinstance(value, float):
                if 'pct' in key or 'rate' in key:
                    formatted_value = f"{value:.2f}%"
                else:
                    formatted_value = f"{value:.4f}"
            else:
                formatted_value = str(value)
            
            # Format key
            formatted_key = key.replace('_', ' ').title()
            
            rows.append(f"<tr><td>{formatted_key}</td><td>{formatted_value}</td></tr>")
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """
    
    def _format_trades_table(self, trades: pd.DataFrame, max_rows: int = 50) -> str:
        """Format trades as HTML table."""
        if len(trades) == 0:
            return "<p>No trades executed.</p>"
        
        # Select recent trades
        recent_trades = trades.tail(max_rows)
        
        rows = []
        for _, trade in recent_trades.iterrows():
            pnl_class = 'positive' if trade.get('pnl', 0) > 0 else 'negative'
            
            row = f"""
            <tr>
                <td>{trade.get('entry_time', '')}</td>
                <td>{trade.get('symbol', '')}</td>
                <td>{trade.get('direction', '')}</td>
                <td>${trade.get('entry_price', 0):.2f}</td>
                <td>${trade.get('exit_price', 0):.2f}</td>
                <td class="{pnl_class}">${trade.get('pnl', 0):.2f}</td>
                <td class="{pnl_class}">{trade.get('pnl_percent', 0):.2f}%</td>
            </tr>
            """
            rows.append(row)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Entry Time</th>
                    <th>Symbol</th>
                    <th>Direction</th>
                    <th>Entry Price</th>
                    <th>Exit Price</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        <p><em>Showing last {len(recent_trades)} of {len(trades)} trades</em></p>
        """
    
    def _create_equity_chart(self, equity_curve: pd.DataFrame) -> str:
        """Create equity curve chart."""
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly not available for charts</p>"
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve['equity'],
            mode='lines',
            name='Equity',
            line=dict(color='#3498db', width=2),
        ))
        
        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Equity ($)',
            hovermode='x unified',
            template='plotly_white',
            height=400,
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='equity_chart')
    
    def _create_drawdown_chart(self, equity_curve: pd.DataFrame) -> str:
        """Create drawdown chart."""
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly not available for charts</p>"
        
        # Calculate drawdown
        rolling_max = equity_curve['equity'].cummax()
        drawdown = (equity_curve['equity'] - rolling_max) / rolling_max * 100
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=drawdown,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='#e74c3c', width=2),
        ))
        
        fig.update_layout(
            title='Drawdown Over Time',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            hovermode='x unified',
            template='plotly_white',
            height=300,
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='drawdown_chart')
    
    def _create_returns_distribution(self, trades: pd.DataFrame) -> str:
        """Create returns distribution histogram."""
        if not PLOTLY_AVAILABLE or len(trades) == 0:
            return "<p>Insufficient data for distribution chart</p>"
        
        returns = trades['pnl_percent'].values
        
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Returns',
            marker=dict(color='#9b59b6'),
        ))
        
        fig.update_layout(
            title='Returns Distribution',
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            template='plotly_white',
            height=300,
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='returns_dist')
    
    def _create_monthly_returns_heatmap(self, equity_curve: pd.DataFrame) -> str:
        """Create monthly returns heatmap."""
        if not PLOTLY_AVAILABLE or len(equity_curve) == 0:
            return "<p>Insufficient data for monthly returns</p>"
        
        # Calculate monthly returns
        equity_curve = equity_curve.copy()
        equity_curve['month'] = equity_curve.index.to_period('M')
        monthly = equity_curve.groupby('month')['equity'].agg(['first', 'last'])
        monthly['return'] = (monthly['last'] - monthly['first']) / monthly['first'] * 100
        
        if len(monthly) == 0:
            return "<p>Insufficient data for monthly returns</p>"
        
        # Create pivot table for heatmap
        monthly_index = monthly.index.to_timestamp()
        monthly['year'] = monthly_index.year
        monthly['month_name'] = monthly_index.strftime('%b')
        
        pivot = monthly.pivot_table(values='return', index='month_name', columns='year')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=np.round(pivot.values, 2),
            texttemplate='%{text}%',
            textfont={"size": 10},
        ))
        
        fig.update_layout(
            title='Monthly Returns Heatmap (%)',
            xaxis_title='Year',
            yaxis_title='Month',
            height=300,
        )
        
        return fig.to_html(include_plotlyjs=False, div_id='monthly_heatmap')
    
    def export_csv_data(
        self,
        equity_curve: pd.DataFrame,
        trades: pd.DataFrame,
        prefix: str = 'backtest',
    ):
        """Export data to CSV files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Export equity curve
        equity_file = self.output_dir / f"{prefix}_equity_{timestamp}.csv"
        equity_curve.to_csv(equity_file)
        logger.info(f"Exported equity curve to {equity_file}")
        
        # Export trades
        if len(trades) > 0:
            trades_file = self.output_dir / f"{prefix}_trades_{timestamp}.csv"
            trades.to_csv(trades_file, index=False)
            logger.info(f"Exported trades to {trades_file}")
