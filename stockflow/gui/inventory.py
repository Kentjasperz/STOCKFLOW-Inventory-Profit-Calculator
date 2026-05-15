"""
Inventory tab – add/edit/delete products, view stock levels, restock.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from stockflow.database import Database
from stockflow.models import Product, RestockRecord

BG_COLOR = "#1e1e2e"
CARD_BG = "#2a2a3e"
ACCENT = "#7c3aed"
TEXT_COLOR = "#e2e8f0"
GREEN = "#22c55e"
YELLOW = "#eab308"
RED = "#ef4444"
MUTED = "#94a3b8"


class InventoryTab(ttk.Frame):
    def __init__(self, parent, db: Database, app):
        super().__init__(parent)
        self.db = db
        self.app = app
        self.configure(style="TFrame")
        self._build()
        self.refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG_COLOR)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        # Toolbar
        toolbar = tk.Frame(outer, bg=BG_COLOR)
        toolbar.pack(fill="x", pady=(0, 8))

        ttk.Button(toolbar, text="+ Add Product",
                   command=self._open_add_dialog).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Edit Selected",
                   command=self._open_edit_dialog).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Delete Selected", style="Danger.TButton",
                   command=self._delete_product).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Restock Selected", style="Success.TButton",
                   command=self._open_restock_dialog).pack(side="left", padx=(0, 6))

        # Search
        tk.Label(toolbar, text="Search:", bg=BG_COLOR, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(toolbar, textvariable=self.search_var, width=24).pack(side="left")

        # Category filter
        tk.Label(toolbar, text="Category:", bg=BG_COLOR, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(12, 4))
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ttk.Combobox(toolbar, textvariable=self.cat_var,
                                      state="readonly", width=16)
        self.cat_combo.pack(side="left")
        self.cat_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_filter())

        # Treeview
        tree_frame = tk.Frame(outer, bg=BG_COLOR)
        tree_frame.pack(fill="both", expand=True)

        cols = ("ID", "Name", "SKU", "Category", "Qty", "Reorder Lvl",
                "Unit Cost", "Unit Price", "Margin %", "Stock Value", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                 selectmode="browse")

        widths = {"ID": 40, "Name": 180, "SKU": 90, "Category": 100,
                  "Qty": 60, "Reorder Lvl": 80, "Unit Cost": 90,
                  "Unit Price": 90, "Margin %": 70,
                  "Stock Value": 100, "Status": 90}
        for col in cols:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths.get(col, 90), anchor="center")
        self.tree.column("Name", anchor="w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Status bar
        self.status_var = tk.StringVar()
        tk.Label(outer, textvariable=self.status_var, bg=BG_COLOR, fg=MUTED,
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(6, 0))

        # Tags for row colouring
        self.tree.tag_configure("oos", foreground=RED)
        self.tree.tag_configure("low", foreground=YELLOW)
        self.tree.tag_configure("ok", foreground=GREEN)

        self._sort_col = None
        self._sort_reverse = False
        self._all_products = []

    # ── Data loading ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._all_products = self.db.get_all_products()
        # Update category filter list
        cats = sorted({p.category for p in self._all_products if p.category})
        self.cat_combo["values"] = ["All"] + cats
        if self.cat_var.get() not in ["All"] + cats:
            self.cat_var.set("All")
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search_var.get().lower()
        cat_filter = self.cat_var.get()
        filtered = [
            p for p in self._all_products
            if (query in p.name.lower() or query in p.sku.lower())
            and (cat_filter == "All" or p.category == cat_filter)
        ]
        self._populate_tree(filtered)

    def _populate_tree(self, products) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for p in products:
            margin = f"{p.profit_margin_pct:.1f}%"
            stock_val = f"${p.inventory_value:,.2f}"
            if p.is_out_of_stock:
                status = "OUT OF STOCK"
                tag = "oos"
            elif p.is_low_stock:
                status = "LOW STOCK"
                tag = "low"
            else:
                status = "OK"
                tag = "ok"
            self.tree.insert("", "end", iid=str(p.id), tags=(tag,), values=(
                p.id, p.name, p.sku, p.category,
                p.quantity, p.reorder_level,
                f"${p.unit_cost:.2f}", f"${p.unit_price:.2f}",
                margin, stock_val, status,
            ))
        total = len(products)
        low = sum(1 for p in products if p.is_low_stock and not p.is_out_of_stock)
        oos = sum(1 for p in products if p.is_out_of_stock)
        self.status_var.set(
            f"{total} products  |  {oos} out-of-stock  |  {low} low-stock"
        )

    # ── Sorting ───────────────────────────────────────────────────────────────

    def _sort_by(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False
        col_map = {
            "ID": "id", "Name": "name", "SKU": "sku", "Category": "category",
            "Qty": "quantity", "Reorder Lvl": "reorder_level",
            "Unit Cost": "unit_cost", "Unit Price": "unit_price",
            "Margin %": "profit_margin_pct",
            "Stock Value": "inventory_value",
        }
        attr = col_map.get(col)
        if attr:
            self._all_products.sort(
                key=lambda p: getattr(p, attr, ""),
                reverse=self._sort_reverse,
            )
        self._apply_filter()

    # ── Selected product helper ───────────────────────────────────────────────

    def _selected_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a product first.")
            return None
        return self.db.get_product(int(sel[0]))

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _open_add_dialog(self) -> None:
        ProductDialog(self, self.db, product=None, on_save=self._after_save)

    def _open_edit_dialog(self) -> None:
        product = self._selected_product()
        if product:
            ProductDialog(self, self.db, product=product, on_save=self._after_save)

    def _delete_product(self) -> None:
        product = self._selected_product()
        if not product:
            return
        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{product.name}'?\nThis will also remove all associated sales records.",
        ):
            self.db.delete_product(product.id)
            self._after_save()

    def _open_restock_dialog(self) -> None:
        product = self._selected_product()
        if product:
            RestockDialog(self, self.db, product, on_save=self._after_save)

    def _after_save(self) -> None:
        self.refresh()
        self.app.dashboard_tab.refresh()


# ── Product dialog ─────────────────────────────────────────────────────────────

class ProductDialog(tk.Toplevel):
    def __init__(self, parent, db: Database, product, on_save):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.on_save = on_save
        self.title("Edit Product" if product else "Add Product")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self.grab_set()
        self._build()
        if product:
            self._populate(product)

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 6}
        form = tk.Frame(self, bg=BG_COLOR, padx=20, pady=20)
        form.pack()

        fields = [
            ("Product Name *", "name"),
            ("SKU *", "sku"),
            ("Category", "category"),
            ("Quantity *", "quantity"),
            ("Reorder Level *", "reorder_level"),
            ("Unit Cost ($) *", "unit_cost"),
            ("Unit Price ($) *", "unit_price"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, bg=BG_COLOR, fg=TEXT_COLOR,
                     font=("Segoe UI", 9), anchor="e", width=18).grid(
                row=i, column=0, sticky="e", **pad)
            var = tk.StringVar()
            self.vars[key] = var
            entry = ttk.Entry(form, textvariable=var, width=28)
            entry.grid(row=i, column=1, sticky="w", **pad)
            if i == 0:
                entry.focus()

        btn_frame = tk.Frame(self, bg=BG_COLOR, pady=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Save", command=self._save).pack(
            side="left", padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side="left", padx=8)

    def _populate(self, p: Product) -> None:
        self.vars["name"].set(p.name)
        self.vars["sku"].set(p.sku)
        self.vars["category"].set(p.category)
        self.vars["quantity"].set(str(p.quantity))
        self.vars["reorder_level"].set(str(p.reorder_level))
        self.vars["unit_cost"].set(f"{p.unit_cost:.2f}")
        self.vars["unit_price"].set(f"{p.unit_price:.2f}")

    def _save(self) -> None:
        name = self.vars["name"].get().strip()
        sku = self.vars["sku"].get().strip()
        category = self.vars["category"].get().strip()
        try:
            quantity = int(self.vars["quantity"].get())
            reorder_level = int(self.vars["reorder_level"].get())
            unit_cost = float(self.vars["unit_cost"].get())
            unit_price = float(self.vars["unit_price"].get())
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Quantity and Reorder Level must be integers.\n"
                                 "Unit Cost and Unit Price must be numbers.")
            return

        if not name or not sku:
            messagebox.showerror("Validation", "Name and SKU are required.")
            return
        if quantity < 0 or reorder_level < 0:
            messagebox.showerror("Validation", "Quantity and Reorder Level cannot be negative.")
            return
        if unit_cost < 0 or unit_price < 0:
            messagebox.showerror("Validation", "Costs and prices cannot be negative.")
            return

        p = Product(
            id=self.product.id if self.product else None,
            name=name, sku=sku, category=category,
            quantity=quantity, reorder_level=reorder_level,
            unit_cost=unit_cost, unit_price=unit_price,
        )
        try:
            if self.product:
                self.db.update_product(p)
            else:
                self.db.add_product(p)
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        self.destroy()
        self.on_save()


# ── Restock dialog ─────────────────────────────────────────────────────────────

class RestockDialog(tk.Toplevel):
    def __init__(self, parent, db: Database, product: Product, on_save):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.on_save = on_save
        self.title(f"Restock: {product.name}")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self.grab_set()
        self._build()

    def _build(self) -> None:
        form = tk.Frame(self, bg=BG_COLOR, padx=24, pady=20)
        form.pack()

        info = (f"Current stock: {self.product.quantity}  |  "
                f"Reorder level: {self.product.reorder_level}")
        tk.Label(form, text=info, bg=BG_COLOR, fg=MUTED,
                 font=("Segoe UI", 9)).grid(row=0, columnspan=2, pady=(0, 12))

        fields = [
            ("Quantity to Add *", "qty"),
            ("Cost per Unit ($) *", "cost"),
            ("Restock Date *", "restock_date"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields, start=1):
            tk.Label(form, text=label, bg=BG_COLOR, fg=TEXT_COLOR,
                     font=("Segoe UI", 9), anchor="e", width=18).grid(
                row=i, column=0, sticky="e", padx=10, pady=6)
            var = tk.StringVar()
            if key == "restock_date":
                var.set(str(date.today()))
            elif key == "cost":
                var.set(f"{self.product.unit_cost:.2f}")
            self.vars[key] = var
            ttk.Entry(form, textvariable=var, width=20).grid(
                row=i, column=1, sticky="w", padx=10, pady=6)

        btn_frame = tk.Frame(self, bg=BG_COLOR, pady=10)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Restock", style="Success.TButton",
                   command=self._save).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side="left", padx=8)

    def _save(self) -> None:
        try:
            qty = int(self.vars["qty"].get())
            cost = float(self.vars["cost"].get())
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Quantity must be an integer; cost must be a number.")
            return
        if qty <= 0:
            messagebox.showerror("Validation", "Quantity to add must be > 0.")
            return
        if cost < 0:
            messagebox.showerror("Validation", "Cost per unit cannot be negative.")
            return

        restock_date = self.vars["restock_date"].get().strip()
        record = RestockRecord(
            product_id=self.product.id,
            product_name=self.product.name,
            quantity_added=qty,
            cost_per_unit=cost,
            restock_date=restock_date,
        )
        try:
            self.db.record_restock(record)
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        self.destroy()
        self.on_save()
