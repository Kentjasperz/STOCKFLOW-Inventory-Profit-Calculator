"""
Dashboard tab – overview KPIs, alerts, and top-products chart.
"""
import tkinter as tk
from tkinter import ttk

from stockflow.database import Database
from stockflow.calculations import restock_recommendations

BG_COLOR = "#1e1e2e"
CARD_BG = "#2a2a3e"
ACCENT = "#7c3aed"
TEXT_COLOR = "#e2e8f0"
GREEN = "#22c55e"
YELLOW = "#eab308"
RED = "#ef4444"
MUTED = "#94a3b8"


class KPICard(tk.Frame):
    """A coloured card displaying a label and a value."""

    def __init__(self, parent, title: str, value: str = "–",
                 accent_color: str = ACCENT, **kwargs):
        super().__init__(parent, bg=CARD_BG, padx=16, pady=14,
                         relief="flat", bd=0, **kwargs)
        tk.Label(self, text=title, font=("Segoe UI", 9), bg=CARD_BG,
                 fg=MUTED).pack(anchor="w")
        self.value_label = tk.Label(
            self, text=value, font=("Segoe UI", 22, "bold"),
            bg=CARD_BG, fg=accent_color,
        )
        self.value_label.pack(anchor="w", pady=(4, 0))

    def set_value(self, value: str) -> None:
        self.value_label.config(text=value)


class DashboardTab(ttk.Frame):
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

        # ── KPI row ───────────────────────────────────────────────────────────
        kpi_row = tk.Frame(outer, bg=BG_COLOR)
        kpi_row.pack(fill="x", pady=(0, 16))

        self.card_products = KPICard(kpi_row, "Total Products", accent_color=ACCENT)
        self.card_inv_value = KPICard(kpi_row, "Inventory Value", accent_color="#3b82f6")
        self.card_revenue = KPICard(kpi_row, "Total Revenue", accent_color=GREEN)
        self.card_profit = KPICard(kpi_row, "Total Profit", accent_color="#f59e0b")
        self.card_low = KPICard(kpi_row, "Low-Stock Items", accent_color=YELLOW)
        self.card_oos = KPICard(kpi_row, "Out-of-Stock", accent_color=RED)

        for card in (self.card_products, self.card_inv_value, self.card_revenue,
                     self.card_profit, self.card_low, self.card_oos):
            card.pack(side="left", expand=True, fill="both", padx=6)

        # ── Lower section: alerts + top products ──────────────────────────────
        lower = tk.Frame(outer, bg=BG_COLOR)
        lower.pack(fill="both", expand=True)
        lower.columnconfigure(0, weight=1)
        lower.columnconfigure(1, weight=1)
        lower.rowconfigure(0, weight=1)

        # Alerts panel
        alert_frame = tk.LabelFrame(
            lower, text="  Stock Alerts", font=("Segoe UI", 10, "bold"),
            bg=CARD_BG, fg=ACCENT, padx=10, pady=10, relief="flat", bd=1,
        )
        alert_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.alert_list = tk.Listbox(
            alert_frame, bg=CARD_BG, fg=TEXT_COLOR,
            font=("Segoe UI", 9), selectbackground="#5b21b6",
            relief="flat", bd=0, activestyle="none",
        )
        scrollbar = ttk.Scrollbar(alert_frame, orient="vertical",
                                  command=self.alert_list.yview)
        self.alert_list.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.alert_list.pack(fill="both", expand=True)

        # Top products panel
        top_frame = tk.LabelFrame(
            lower, text="  Top 5 Products by Revenue", font=("Segoe UI", 10, "bold"),
            bg=CARD_BG, fg=ACCENT, padx=10, pady=10, relief="flat", bd=1,
        )
        top_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        cols = ("Product", "Revenue")
        self.top_tree = ttk.Treeview(top_frame, columns=cols, show="headings",
                                     height=8)
        for col in cols:
            self.top_tree.heading(col, text=col)
        self.top_tree.column("Product", width=220)
        self.top_tree.column("Revenue", width=120, anchor="e")
        self.top_tree.pack(fill="both", expand=True)

        # Restock recommendations panel
        rec_frame = tk.LabelFrame(
            outer, text="  Restock Recommendations", font=("Segoe UI", 10, "bold"),
            bg=CARD_BG, fg=ACCENT, padx=10, pady=10, relief="flat", bd=1,
        )
        rec_frame.pack(fill="x", pady=(16, 0))

        rec_cols = ("Product", "SKU", "Current Qty", "Reorder Level",
                    "Suggested Qty", "Est. Restock Cost")
        self.rec_tree = ttk.Treeview(rec_frame, columns=rec_cols,
                                     show="headings", height=5)
        for col in rec_cols:
            self.rec_tree.heading(col, text=col)
            self.rec_tree.column(col, width=160, anchor="center")
        self.rec_tree.column("Product", width=200, anchor="w")
        self.rec_tree.pack(fill="x", expand=True)

    # ── Data refresh ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        stats = self.db.get_summary_stats()
        self.card_products.set_value(str(stats["total_products"]))
        self.card_inv_value.set_value(f"${stats['inventory_value']:,.2f}")
        self.card_revenue.set_value(f"${stats['total_revenue']:,.2f}")
        self.card_profit.set_value(f"${stats['total_profit']:,.2f}")
        self.card_low.set_value(str(stats["low_stock_count"]))
        self.card_oos.set_value(str(stats["out_of_stock_count"]))

        # Alerts
        self.alert_list.delete(0, "end")
        low_products = self.db.get_low_stock_products()
        if not low_products:
            self.alert_list.insert("end", "  All items are sufficiently stocked.")
            self.alert_list.itemconfig(0, fg=GREEN)
        else:
            for p in low_products:
                if p.is_out_of_stock:
                    msg = f"  OUT OF STOCK  |  {p.name} (SKU: {p.sku})"
                    colour = RED
                else:
                    msg = (f"  LOW STOCK     |  {p.name} (SKU: {p.sku})"
                           f"  –  {p.quantity} left  (reorder at {p.reorder_level})")
                    colour = YELLOW
                self.alert_list.insert("end", msg)
                self.alert_list.itemconfig("end", fg=colour)

        # Top products
        for row in self.top_tree.get_children():
            self.top_tree.delete(row)
        for name, rev in self.db.get_top_products_by_revenue():
            self.top_tree.insert("", "end", values=(name, f"${rev:,.2f}"))

        # Restock recommendations
        for row in self.rec_tree.get_children():
            self.rec_tree.delete(row)
        products = self.db.get_all_products()
        recs = restock_recommendations(products)
        if not recs:
            self.rec_tree.insert("", "end",
                                 values=("No restock needed", "", "", "", "", ""))
        else:
            for r in recs:
                self.rec_tree.insert("", "end", values=(
                    r["name"],
                    r["sku"],
                    r["current_qty"],
                    r["reorder_level"],
                    r["suggested_qty"],
                    f"${r['estimated_cost']:,.2f}",
                ))
