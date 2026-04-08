"""
Main application window for STOCKFLOW.
"""
import tkinter as tk
from tkinter import ttk

from stockflow.database import Database
from stockflow.gui.dashboard import DashboardTab
from stockflow.gui.inventory import InventoryTab
from stockflow.gui.sales import SalesTab
from stockflow.gui.profits import ProfitsTab

# Colour palette
BG_COLOR = "#1e1e2e"
TAB_BG = "#2a2a3e"
ACCENT = "#7c3aed"
TEXT_COLOR = "#e2e8f0"
HEADER_BG = "#16213e"


class StockFlowApp(tk.Tk):
    """Root window – hosts the tabbed notebook and shared database."""

    def __init__(self, db_path: str = None):
        super().__init__()
        self.title("STOCKFLOW – Inventory & Profit Calculator")
        self.geometry("1280x780")
        self.minsize(1024, 680)
        self.configure(bg=BG_COLOR)

        self.db = Database(db_path) if db_path else Database()
        self._setup_styles()
        self._build_header()
        self._build_notebook()
        self._populate_tabs()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=TAB_BG,
            foreground=TEXT_COLOR,
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT), ("active", "#5b21b6")],
            foreground=[("selected", "white")],
        )
        style.configure("TFrame", background=BG_COLOR)
        style.configure(
            "Treeview",
            background="#2a2a3e",
            foreground=TEXT_COLOR,
            fieldbackground="#2a2a3e",
            rowheight=28,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=ACCENT,
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#5b21b6")])
        style.configure(
            "TButton",
            background=ACCENT,
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6],
        )
        style.map("TButton", background=[("active", "#5b21b6")])
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("TEntry", fieldbackground="#2a2a3e", foreground=TEXT_COLOR)
        style.configure(
            "TCombobox",
            fieldbackground="#2a2a3e",
            foreground=TEXT_COLOR,
            background=TAB_BG,
        )
        style.configure("TLabelframe", background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure(
            "TLabelframe.Label",
            background=BG_COLOR,
            foreground=ACCENT,
            font=("Segoe UI", 10, "bold"),
        )

        # Danger button for delete actions
        style.configure(
            "Danger.TButton",
            background="#dc2626",
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6],
        )
        style.map("Danger.TButton", background=[("active", "#b91c1c")])

        # Success (green) button
        style.configure(
            "Success.TButton",
            background="#16a34a",
            foreground="white",
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
            padding=[10, 6],
        )
        style.map("Success.TButton", background=[("active", "#15803d")])

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=HEADER_BG, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="  STOCKFLOW",
            font=("Segoe UI", 20, "bold"),
            bg=HEADER_BG,
            fg=ACCENT,
        ).pack(side="left", padx=10)

        tk.Label(
            header,
            text="Inventory & Profit Calculator",
            font=("Segoe UI", 11),
            bg=HEADER_BG,
            fg=TEXT_COLOR,
        ).pack(side="left")

    # ── Notebook ──────────────────────────────────────────────────────────────

    def _build_notebook(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

    def _populate_tabs(self) -> None:
        self.dashboard_tab = DashboardTab(self.notebook, self.db, self)
        self.inventory_tab = InventoryTab(self.notebook, self.db, self)
        self.sales_tab = SalesTab(self.notebook, self.db, self)
        self.profits_tab = ProfitsTab(self.notebook, self.db, self)

        self.notebook.add(self.dashboard_tab, text="  Dashboard  ")
        self.notebook.add(self.inventory_tab, text="  Inventory  ")
        self.notebook.add(self.sales_tab, text="  Sales  ")
        self.notebook.add(self.profits_tab, text="  Profits & Trends  ")

        # Refresh dashboard whenever a tab is switched to it
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event) -> None:
        tab = self.notebook.select()
        name = self.notebook.tab(tab, "text").strip()
        if "Dashboard" in name:
            self.dashboard_tab.refresh()
        elif "Profits" in name:
            self.profits_tab.refresh()

    def refresh_all(self) -> None:
        """Called by child tabs after data changes."""
        self.dashboard_tab.refresh()
        self.inventory_tab.refresh()
        self.sales_tab.refresh()
