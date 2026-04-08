"""
Profits & Trends tab – charts and analytics.
"""
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

from stockflow.database import Database
from stockflow.calculations import summarize_trend, moving_average

BG_COLOR = "#1e1e2e"
CARD_BG = "#2a2a3e"
ACCENT = "#7c3aed"
TEXT_COLOR = "#e2e8f0"
GREEN = "#22c55e"
YELLOW = "#eab308"
MUTED = "#94a3b8"

CHART_BG = "#2a2a3e"
CHART_FG = "#e2e8f0"
GRID_COLOR = "#3f3f5a"


def _apply_dark_style(fig, ax):
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_BG)
    ax.tick_params(colors=CHART_FG, labelsize=8)
    ax.xaxis.label.set_color(CHART_FG)
    ax.yaxis.label.set_color(CHART_FG)
    ax.title.set_color(CHART_FG)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)


class ProfitsTab(ttk.Frame):
    def __init__(self, parent, db: Database, app):
        super().__init__(parent)
        self.db = db
        self.app = app
        self.configure(style="TFrame")
        self._build()
        self.refresh()

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG_COLOR)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        # Summary stats row
        stats_row = tk.Frame(outer, bg=BG_COLOR)
        stats_row.pack(fill="x", pady=(0, 12))

        self.stat_vars = {}
        stat_labels = [
            ("total_revenue", "Total Revenue", "$0.00"),
            ("total_profit", "Total Profit", "$0.00"),
            ("overall_margin_pct", "Overall Margin", "0.0%"),
            ("avg_daily_revenue", "Avg Daily Revenue", "$0.00"),
            ("best_day", "Best Day", "–"),
        ]
        for key, label, default in stat_labels:
            card = tk.Frame(stats_row, bg=CARD_BG, padx=14, pady=10)
            card.pack(side="left", expand=True, fill="both", padx=5)
            tk.Label(card, text=label, bg=CARD_BG, fg=MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
            var = tk.StringVar(value=default)
            self.stat_vars[key] = var
            tk.Label(card, textvariable=var, bg=CARD_BG, fg=ACCENT,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(2, 0))

        # View toggle
        toggle_row = tk.Frame(outer, bg=BG_COLOR)
        toggle_row.pack(fill="x", pady=(0, 8))

        tk.Label(toggle_row, text="View:", bg=BG_COLOR, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        self.view_var = tk.StringVar(value="daily")
        for text, val in [("Daily", "daily"), ("Monthly", "monthly")]:
            ttk.Radiobutton(
                toggle_row, text=text, variable=self.view_var, value=val,
                command=self._redraw_charts,
            ).pack(side="left", padx=4)

        # Charts container (2 columns)
        charts_frame = tk.Frame(outer, bg=BG_COLOR)
        charts_frame.pack(fill="both", expand=True)
        charts_frame.columnconfigure(0, weight=3)
        charts_frame.columnconfigure(1, weight=2)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.rowconfigure(1, weight=1)

        # Revenue/Profit over time (spans top row)
        self.fig_trend, self.ax_trend = plt.subplots(figsize=(7, 3))
        self.canvas_trend = FigureCanvasTkAgg(self.fig_trend, charts_frame)
        self.canvas_trend.get_tk_widget().grid(
            row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))

        # Top products pie chart
        self.fig_pie, self.ax_pie = plt.subplots(figsize=(4, 3))
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, charts_frame)
        self.canvas_pie.get_tk_widget().grid(
            row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))

        # Profit margin bars
        self.fig_margin, self.ax_margin = plt.subplots(figsize=(7, 3))
        self.canvas_margin = FigureCanvasTkAgg(self.fig_margin, charts_frame)
        self.canvas_margin.get_tk_widget().grid(
            row=1, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))

        # Inventory value by category
        self.fig_cat, self.ax_cat = plt.subplots(figsize=(4, 3))
        self.canvas_cat = FigureCanvasTkAgg(self.fig_cat, charts_frame)
        self.canvas_cat.get_tk_widget().grid(
            row=1, column=1, sticky="nsew", padx=(6, 0), pady=(6, 0))

    # ── Refresh ────────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        daily = self.db.get_daily_sales_summary()
        summary = summarize_trend(daily)
        self.stat_vars["total_revenue"].set(f"${summary['total_revenue']:,.2f}")
        self.stat_vars["total_profit"].set(f"${summary['total_profit']:,.2f}")
        self.stat_vars["overall_margin_pct"].set(
            f"{summary['overall_margin_pct']:.1f}%")
        self.stat_vars["avg_daily_revenue"].set(
            f"${summary['avg_daily_revenue']:,.2f}")
        self.stat_vars["best_day"].set(summary["best_day"] or "–")
        self._redraw_charts()

    def _redraw_charts(self) -> None:
        self._draw_trend_chart()
        self._draw_pie_chart()
        self._draw_margin_chart()
        self._draw_category_chart()

    # ── Revenue/Profit trend ──────────────────────────────────────────────────

    def _draw_trend_chart(self) -> None:
        self.ax_trend.clear()
        _apply_dark_style(self.fig_trend, self.ax_trend)

        view = self.view_var.get()
        if view == "daily":
            data = self.db.get_daily_sales_summary()
            xlabel = "Date"
        else:
            data = self.db.get_monthly_sales_summary()
            xlabel = "Month"

        if not data:
            self.ax_trend.text(0.5, 0.5, "No sales data yet",
                               ha="center", va="center", color=MUTED,
                               transform=self.ax_trend.transAxes)
            self.canvas_trend.draw()
            return

        labels = [d[0] for d in data]
        revenues = [d[1] for d in data]
        profits = [d[2] for d in data]
        x = range(len(labels))

        self.ax_trend.bar(x, revenues, label="Revenue", color=ACCENT,
                          alpha=0.7, zorder=2)
        self.ax_trend.bar(x, profits, label="Profit", color=GREEN,
                          alpha=0.9, zorder=3)

        # Moving average overlay for revenue
        if len(revenues) >= 3:
            ma = moving_average(revenues, window=3)
            self.ax_trend.plot(list(x), ma, color=YELLOW, linewidth=1.5,
                               linestyle="--", label="3-period MA", zorder=4)

        self.ax_trend.set_xticks(list(x))
        self.ax_trend.set_xticklabels(
            labels, rotation=35, ha="right", fontsize=7)
        self.ax_trend.set_title("Revenue & Profit Over Time", fontsize=9)
        self.ax_trend.set_xlabel(xlabel, fontsize=8)
        self.ax_trend.set_ylabel("Amount ($)", fontsize=8)
        self.ax_trend.legend(fontsize=7, facecolor=CHART_BG,
                             labelcolor=CHART_FG, framealpha=0.6)
        self.fig_trend.tight_layout()
        self.canvas_trend.draw()

    # ── Top-products pie ──────────────────────────────────────────────────────

    def _draw_pie_chart(self) -> None:
        self.ax_pie.clear()
        self.fig_pie.patch.set_facecolor(CHART_BG)
        self.ax_pie.set_facecolor(CHART_BG)

        data = self.db.get_top_products_by_revenue(limit=6)
        if not data:
            self.ax_pie.text(0.5, 0.5, "No sales data yet",
                             ha="center", va="center", color=MUTED,
                             transform=self.ax_pie.transAxes)
            self.canvas_pie.draw()
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]
        colors = ["#7c3aed", "#3b82f6", "#22c55e", "#eab308",
                  "#ef4444", "#f97316"][:len(labels)]

        wedges, texts, autotexts = self.ax_pie.pie(
            values, labels=None, autopct="%1.1f%%",
            colors=colors, startangle=140,
            wedgeprops={"linewidth": 0.5, "edgecolor": CHART_BG},
        )
        for at in autotexts:
            at.set_fontsize(7)
            at.set_color(CHART_FG)

        self.ax_pie.legend(
            wedges, labels, loc="lower center",
            bbox_to_anchor=(0.5, -0.12), ncol=2,
            fontsize=6, facecolor=CHART_BG, labelcolor=CHART_FG,
            framealpha=0.6,
        )
        self.ax_pie.set_title("Revenue Share by Product", fontsize=9,
                              color=CHART_FG)
        self.fig_pie.tight_layout()
        self.canvas_pie.draw()

    # ── Profit margin per product ─────────────────────────────────────────────

    def _draw_margin_chart(self) -> None:
        self.ax_margin.clear()
        _apply_dark_style(self.fig_margin, self.ax_margin)

        products = self.db.get_all_products()
        if not products:
            self.ax_margin.text(0.5, 0.5, "No products yet",
                                ha="center", va="center", color=MUTED,
                                transform=self.ax_margin.transAxes)
            self.canvas_margin.draw()
            return

        products_sorted = sorted(products, key=lambda p: p.profit_margin_pct,
                                 reverse=True)[:12]
        names = [p.name[:16] for p in products_sorted]
        margins = [p.profit_margin_pct for p in products_sorted]
        bar_colors = [GREEN if m >= 20 else YELLOW if m >= 10 else "#ef4444"
                      for m in margins]

        x = range(len(names))
        bars = self.ax_margin.barh(list(x), margins, color=bar_colors,
                                   alpha=0.85, zorder=2)
        self.ax_margin.set_yticks(list(x))
        self.ax_margin.set_yticklabels(names, fontsize=7)
        self.ax_margin.axvline(x=20, color=MUTED, linestyle="--",
                               linewidth=0.8, alpha=0.7)
        self.ax_margin.set_title("Profit Margin by Product (%)", fontsize=9)
        self.ax_margin.set_xlabel("Margin (%)", fontsize=8)
        self.fig_margin.tight_layout()
        self.canvas_margin.draw()

    # ── Inventory value by category ────────────────────────────────────────────

    def _draw_category_chart(self) -> None:
        self.ax_cat.clear()
        _apply_dark_style(self.fig_cat, self.ax_cat)

        products = self.db.get_all_products()
        if not products:
            self.ax_cat.text(0.5, 0.5, "No products yet",
                             ha="center", va="center", color=MUTED,
                             transform=self.ax_cat.transAxes)
            self.canvas_cat.draw()
            return

        category_value = {}
        for p in products:
            cat = p.category or "Uncategorized"
            category_value[cat] = category_value.get(cat, 0) + p.inventory_value

        cats = list(category_value.keys())
        vals = [category_value[c] for c in cats]
        colors = ["#7c3aed", "#3b82f6", "#22c55e", "#eab308",
                  "#ef4444", "#f97316"][:len(cats)]

        x = range(len(cats))
        self.ax_cat.bar(list(x), vals, color=colors[:len(cats)],
                        alpha=0.85, zorder=2)
        self.ax_cat.set_xticks(list(x))
        self.ax_cat.set_xticklabels(cats, rotation=20, ha="right", fontsize=7)
        self.ax_cat.set_title("Inventory Value by Category ($)", fontsize=9)
        self.ax_cat.set_ylabel("Value ($)", fontsize=8)
        self.fig_cat.tight_layout()
        self.canvas_cat.draw()
