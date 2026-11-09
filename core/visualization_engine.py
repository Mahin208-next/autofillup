"""
Plotly interactive visualization engine for SurveyForge AI.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


class VisualizationEngine:
    """Creates interactive academic research charts using Plotly."""

    COLOR_PALETTE = ["#1e3a8a", "#0284c7", "#0d9488", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"]

    @staticmethod
    def bar_chart(
        df: pd.DataFrame,
        x_col: str,
        title: Optional[str] = None,
        color_col: Optional[str] = None
    ) -> go.Figure:
        """Create bar chart with percentage / count tooltips."""
        clean = df[x_col].dropna().value_counts().reset_index()
        clean.columns = [x_col, "Count"]
        clean["Percentage"] = (clean["Count"] / clean["Count"].sum() * 100).round(1)

        fig = px.bar(
            clean,
            x=x_col,
            y="Count",
            text="Percentage",
            title=title or f"Distribution of {x_col}",
            color_discrete_sequence=VisualizationEngine.COLOR_PALETTE
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis_title=x_col,
            yaxis_title="Count"
        )
        return fig

    @staticmethod
    def pie_chart(
        df: pd.DataFrame,
        col: str,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create donut / pie chart."""
        counts = df[col].dropna().value_counts().reset_index()
        counts.columns = [col, "Count"]

        fig = px.pie(
            counts,
            names=col,
            values="Count",
            hole=0.4,
            title=title or f"Proportion of {col}",
            color_discrete_sequence=VisualizationEngine.COLOR_PALETTE
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=30)
        )
        return fig

    @staticmethod
    def histogram(
        df: pd.DataFrame,
        col: str,
        bins: int = 20,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create histogram with KDE / distribution overlay."""
        sub = pd.to_numeric(df[col], errors="coerce").dropna()
        fig = px.histogram(
            sub,
            x=col,
            nbins=bins,
            marginal="box",
            title=title or f"Distribution & Spread of {col}",
            color_discrete_sequence=["#0284c7"]
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=30),
            xaxis_title=col,
            yaxis_title="Frequency"
        )
        return fig

    @staticmethod
    def box_plot(
        df: pd.DataFrame,
        y_col: str,
        x_col: Optional[str] = None,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create box and whisker plot."""
        fig = px.box(
            df,
            x=x_col,
            y=y_col,
            color=x_col,
            title=title or f"Box Plot of {y_col}" + (f" grouped by {x_col}" if x_col else ""),
            color_discrete_sequence=VisualizationEngine.COLOR_PALETTE
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=30)
        )
        return fig

    @staticmethod
    def scatter_plot(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        color_col: Optional[str] = None,
        title: Optional[str] = None,
        add_trendline: bool = True
    ) -> go.Figure:
        """Create scatter plot with trendline."""
        sub = df[[x_col, y_col] + ([color_col] if color_col else [])].dropna()
        sub[x_col] = pd.to_numeric(sub[x_col], errors="coerce")
        sub[y_col] = pd.to_numeric(sub[y_col], errors="coerce")
        sub = sub.dropna()

        fig = px.scatter(
            sub,
            x=x_col,
            y=y_col,
            color=color_col,
            trendline="ols" if add_trendline and len(sub) > 5 else None,
            title=title or f"Scatter: {x_col} vs {y_col}",
            color_discrete_sequence=VisualizationEngine.COLOR_PALETTE,
            opacity=0.65
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=30)
        )
        return fig

    @staticmethod
    def correlation_heatmap(
        corr_matrix: pd.DataFrame,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create correlation heatmap."""
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1.0,
            zmax=1.0,
            title=title or "Bivariate Correlation Heatmap Matrix"
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig

