"""
数据可视化模块
提供K线图、成交量图等技术分析图表
"""
import pandas as pd
import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# 可选依赖
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly 未安装，请运行: pip install plotly")

try:
    import mplfinance as mpf
    MPF_AVAILABLE = True
except ImportError:
    MPF_AVAILABLE = False
    logger.warning("mplfinance 未安装，请运行: pip install mplfinance")


class DataVisualizer:
    """数据可视化工具"""

    def __init__(self):
        if not PLOTLY_AVAILABLE:
            logger.warning("plotly 未安装，可视化功能受限")

    def plot_candlestick(
        self,
        df: pd.DataFrame,
        stock_code: str,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        width: int = 1200,
        height: int = 800
    ) -> go.Figure:
        """
        绘制K线图（Plotly交互式）
        
        Args:
            df: 数据DataFrame
            stock_code: 股票代码
            title: 图表标题
            save_path: 保存路径（HTML文件）
            width: 宽度
            height: 高度
            
        Returns:
            Plotly Figure对象
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly 未安装，请运行: pip install plotly")

        if df.empty:
            raise ValueError("数据为空")

        # 准备数据
        df = df.sort_values('date').copy()
        
        if title is None:
            title = f"{stock_code} K线图"

        # 创建子图：上面是K线，下面是成交量
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=('价格', '成交量'),
            row_heights=[0.7, 0.3]  # K线占70%，成交量占30%
        )

        # K线
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线',
            increasing_line_color='red',
            decreasing_line_color='green'
        ), row=1, col=1)

        # 成交量
        colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green' 
                  for i in range(len(df))]
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='成交量',
            marker_color=colors,
            showlegend=False
        ), row=2, col=1)

        # 布局
        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=False,
            width=width,
            height=height,
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Y轴设置
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        
        # X轴设置
        fig.update_xaxes(
            title_text="日期",
            row=2, col=1,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label='1M', step='month', stepmode='backward'),
                    dict(count=3, label='3M', step='month', stepmode='backward'),
                    dict(count=6, label='6M', step='month', stepmode='backward'),
                    dict(count=1, label='1Y', step='year', stepmode='backward'),
                    dict(step='all', label='ALL')
                ]
            )
        )

        # 保存
        if save_path:
            fig.write_html(save_path)
            logger.info(f"K线图已保存: {save_path}")

        return fig

    def plot_line(
        self,
        df: pd.DataFrame,
        columns: List[str],
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        width: int = 1000,
        height: int = 600
    ) -> go.Figure:
        """
        绘制折线图
        
        Args:
            df: 数据DataFrame
            columns: 要绘制的列名
            title: 图表标题
            save_path: 保存路径
            width: 宽度
            height: 高度
            
        Returns:
            Plotly Figure对象
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly 未安装")

        df = df.sort_values('date').copy()
        
        fig = go.Figure()
        
        for col in columns:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[col],
                    mode='lines',
                    name=col
                ))

        fig.update_layout(
            title=title or '折线图',
            xaxis_title='日期',
            yaxis_title='值',
            width=width,
            height=height,
            template='plotly_white'
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"折线图已保存: {save_path}")

        return fig

    def plot_volume(
        self,
        df: pd.DataFrame,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        width: int = 1000,
        height: int = 400
    ) -> go.Figure:
        """
        绘制成交量图
        
        Args:
            df: 数据DataFrame
            title: 图表标题
            save_path: 保存路径
            width: 宽度
            height: 高度
            
        Returns:
            Plotly Figure对象
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly 未安装")

        df = df.sort_values('date').copy()
        
        colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green' 
                  for i in range(len(df))]

        fig = go.Figure(data=[
            go.Bar(
                x=df['date'],
                y=df['volume'],
                marker_color=colors,
                name='成交量'
            )
        ])

        fig.update_layout(
            title=title or '成交量',
            xaxis_title='日期',
            yaxis_title='成交量',
            width=width,
            height=height,
            template='plotly_white'
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"成交量图已保存: {save_path}")

        return fig

    def plot_ma(
        self,
        df: pd.DataFrame,
        stock_code: str,
        ma_periods: List[int] = [5, 10, 20, 60],
        save_path: Optional[str] = None
    ) -> go.Figure:
        """
        绘制带均线的K线图
        
        Args:
            df: 数据DataFrame
            stock_code: 股票代码
            ma_periods: 均线周期列表
            save_path: 保存路径
            
        Returns:
            Plotly Figure对象
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly 未安装")

        df = df.sort_values('date').copy()

        # 计算均线
        for period in ma_periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()

        # 使用子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=('价格 + 均线', '成交量'),
            row_heights=[0.7, 0.3]
        )

        # K线
        fig.add_trace(go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线',
            increasing_line_color='red',
            decreasing_line_color='green'
        ), row=1, col=1)

        # 均线
        colors = ['orange', 'blue', 'purple', 'brown']
        for i, period in enumerate(ma_periods):
            if f'MA{period}' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[f'MA{period}'],
                    mode='lines',
                    name=f'MA{period}',
                    line=dict(color=colors[i % len(colors)], width=1.5)
                ), row=1, col=1)

        # 成交量
        colors = ['red' if df['close'].iloc[i] >= df['open'].iloc[i] else 'green' 
                  for i in range(len(df))]
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='成交量',
            marker_color=colors,
            showlegend=False
        ), row=2, col=1)

        fig.update_layout(
            title=f"{stock_code} K线图 + 均线",
            xaxis_rangeslider_visible=False,
            template='plotly_white',
            height=800
        )

        if save_path:
            fig.write_html(save_path)
            logger.info(f"均线图已保存: {save_path}")

        return fig


def plot_candlestick_mpl(
    df: pd.DataFrame,
    save_path: Optional[str] = None,
    style: str = 'yahoo',
    title: str = 'K线图'
):
    """
    使用mplfinance绘制K线图（静态图）
    
    Args:
        df: 数据DataFrame（需要包含 open, high, low, close 列）
        save_path: 保存路径（PNG/SVG）
        style: 样式风格
        title: 标题
    """
    if not MPF_AVAILABLE:
        raise ImportError("mplfinance 未安装，请运行: pip install mplfinance")

    # 准备数据（mplfinance需要特定列名）
    mpf_df = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
    mpf_df = mpf_df.set_index('date')
    mpf_df.index = pd.to_datetime(mpf_df.index)

    # 绘图
    mc = mpf.make_marketcolors(
        up='red',
        down='green',
        edge='inherit',
        wick='inherit',
        volume='in'
    )
    s = mpf.make_mpf_style(marketcolors=mc)

    if save_path:
        mpf.plot(mpf_df, type='candle', style=s, savefig=save_path, title=title)
        logger.info(f"K线图已保存: {save_path}")
    else:
        return mpf.plot(mpf_df, type='candle', style=s, returnfig=True)
