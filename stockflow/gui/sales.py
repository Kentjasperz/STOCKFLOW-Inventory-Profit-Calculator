"""
Sales tab – record sales and view transaction history.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from stockflow.database import Database
from stockflow.models import Sale

BG_COLOR = "#1e1e2e"
CARD_BG = "#2a2a3e"
ACCENT = "#7c3aed"
TEXT_COLOR = "#e2e8f0"
GREEN = "#22c55e"
RED = "#ef4444"
MUTED = "#94a3b8"


class SalesTab(ttk.Frame):
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

        # ── Record Sale form ──────────────────────────────────────────────────
        form_frame = tk.LabelFrame(
            outer, text="  Record a Sale", font=("Segoe UI", 10, "bold"),
            bg=CARD_BG, fg=ACCENT, padx=14, pady=12, relief="flat", bd=1,
        )
        form_frame.pack(fill="x", pady=(0, 14))

        # Row 1
        r1 = tk.Frame(form_frame, bg=CARD_BG)
        r1.pack(fill="x", pady=4)

        tk.Label(r1, text="Product:", bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.product_var = tk.StringVar()
        self.product_combo = ttk.Combobox(r1, textvariable=self.product_var,
                                          state="readonly", width=30)
        self.product_combo.pack(side="left", padx=(0, 20))
        self.product_combo.bind("<<ComboboxSelected>>", self._on_product_selected)

        tk.Label(r1, text="Qty Sold:", bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.qty_var = tk.StringVar(value="1")
        ttk.Entry(r1, textvariable=self.qty_var, width=8).pack(side="left", padx=(0, 20))

        tk.Label(r1, text="Sale Price ($):", bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.price_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self.price_var, width=10).pack(side="left", padx=(0, 20))

        tk.Label(r1, text="Date:", bg=CARD_BG, fg=TEXT_COLOR,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self.date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(r1, textvariable=self.date_var, width=12).pack(side="left", padx=(0, 20))

        ttk.Button(r1, text="Record Sale", style="Success.TButton",
                   command=self._record_sale).pack(side="left")

        # Stock info label
        self.stock_info_var = tk.StringVar(value="")
        tk.Label(form_frame, textvariable=self.stock_info_var,
                 bg=CARD_BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        # ── Sales history ─────────────────────────────────────────────────────
        hist_frame = tk.LabelFrame(
            outer, text="  Sales History", font=("Segoe UI", 10, "bold"),
            bg=CARD_BG, fg=ACCENT, padx=10, pady=10, relief="flat", bd=1,
        )
        hist_frame.pack(fill="both", expand=True)

        cols = ("ID", "Date", "Product", "Qty Sold", "Unit Cost",
                "Sale Price", "Revenue", "Profit", "Margin %")
        self.tree = ttk.Treeview(hist_frame, columns=cols, show="headings",
                                 selectmode="browse")

        widths = {"ID": 40, "Date": 90, "Product": 180, "Qty Sold": 70,
                  "Unit Cost": 90, "Sale Price": 90, "Revenue": 100,
                  "Profit": 90, "Margin %": 70}
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths.get(col, 90), anchor="center")
        self.tree.column("Product", anchor="w")

        vsb = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Totals bar
        totals_frame = tk.Frame(outer, bg=BG_COLOR)
        totals_frame.pack(fill="x", pady=(8, 0))

        self.total_revenue_var = tk.StringVar()
        self.total_profit_var = tk.StringVar()
        self.total_margin_var = tk.StringVar()

        for label_text, var in [
            ("Total Revenue:", self.total_revenue_var),
            ("Total Profit:", self.total_profit_var),
            ("Avg Margin:", self.total_margin_var),
        ]:
            tk.Label(totals_frame, text=label_text, bg=BG_COLOR, fg=MUTED,
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
            tk.Label(totals_frame, textvariable=var, bg=BG_COLOR, fg=GREEN,
                     font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 24))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_products_combo(self) -> None:
        products = self.db.get_all_products()
        self._product_map = {f"{p.name} (SKU: {p.sku})": p for p in products}
        self.product_combo["values"] = list(self._product_map.keys())

    def _on_product_selected(self, event=None) -> None:
        key = self.product_var.get()
        p = self._product_map.get(key)
        if p:
            self.price_var.set(f"{p.unit_price:.2f}")
            self.stock_info_var.set(
                f"Current stock: {p.quantity}  |  Cost: ${p.unit_cost:.2f}"
                f"  |  Default price: ${p.unit_price:.2f}"
            )

    def refresh(self) -> None:
        self._load_products_combo()
        sales = self.db.get_all_sales()
        for row in self.tree.get_children():
            self.tree.delete(row)
        total_rev = 0.0
        total_profit = 0.0
        for s in sales:
            self.tree.insert("", "end", values=(
                s.id, s.sale_date, s.product_name,
                s.quantity_sold,
                f"${s.unit_cost:.2f}", f"${s.sale_price:.2f}",
                f"${s.total_revenue:,.2f}",
                f"${s.gross_profit:,.2f}",
                f"{s.profit_margin_pct:.1f}%",
            ))
            total_rev += s.total_revenue
            total_profit += s.gross_profit

        self.total_revenue_var.set(f"${total_rev:,.2f}")
        self.total_profit_var.set(f"${total_profit:,.2f}")
        margin = (total_profit / total_rev * 100) if total_rev else 0.0
        self.total_margin_var.set(f"{margin:.1f}%")

    # ── Record sale ───────────────────────────────────────────────────────────

    def _record_sale(self) -> None:
        key = self.product_var.get()
        if not key:
            messagebox.showerror("Validation", "Please select a product.")
            return
        product = self._product_map.get(key)
        if not product:
            messagebox.showerror("Validation", "Invalid product selected.")
            return
        try:
            qty = int(self.qty_var.get())
            price = float(self.price_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Quantity must be an integer and price must be a number.")
            return
        if qty <= 0:
            messagebox.showerror("Validation", "Quantity must be greater than 0.")
            return
        if price < 0:
            messagebox.showerror("Validation", "Sale price cannot be negative.")
            return
        if qty > product.quantity:
            messagebox.showerror(
                "Insufficient Stock",
                f"Only {product.quantity} units of '{product.name}' in stock.",
            )
            return

        sale_date = self.date_var.get().strip() or str(date.today())
        sale = Sale(
            product_id=product.id,
            product_name=product.name,
            quantity_sold=qty,
            unit_cost=product.unit_cost,
            sale_price=price,
            sale_date=sale_date,
        )
        try:
            self.db.record_sale(sale)
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        messagebox.showinfo(
            "Sale Recorded",
            f"Sold {qty}x {product.name} @ ${price:.2f}\n"
            f"Revenue: ${qty * price:,.2f}  |  "
            f"Profit: ${qty * (price - product.unit_cost):,.2f}",
        )
        self.qty_var.set("1")
        self.product_var.set("")
        self.price_var.set("")
        self.stock_info_var.set("")
        self.app.refresh_all()
