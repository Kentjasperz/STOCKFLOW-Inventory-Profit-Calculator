"""
Database layer for STOCKFLOW using SQLite.
"""
import sqlite3
import os
from datetime import date
from typing import List, Optional, Tuple

from stockflow.models import Product, Sale, RestockRecord

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "stockflow.db")


class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    sku         TEXT    NOT NULL UNIQUE,
                    category    TEXT    NOT NULL DEFAULT '',
                    quantity    INTEGER NOT NULL DEFAULT 0,
                    reorder_level INTEGER NOT NULL DEFAULT 5,
                    unit_cost   REAL    NOT NULL DEFAULT 0.0,
                    unit_price  REAL    NOT NULL DEFAULT 0.0,
                    created_at  TEXT    NOT NULL DEFAULT (date('now')),
                    updated_at  TEXT    NOT NULL DEFAULT (date('now'))
                );

                CREATE TABLE IF NOT EXISTS sales (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id      INTEGER NOT NULL REFERENCES products(id),
                    product_name    TEXT    NOT NULL,
                    quantity_sold   INTEGER NOT NULL,
                    unit_cost       REAL    NOT NULL,
                    sale_price      REAL    NOT NULL,
                    sale_date       TEXT    NOT NULL DEFAULT (date('now'))
                );

                CREATE TABLE IF NOT EXISTS restock_records (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id      INTEGER NOT NULL REFERENCES products(id),
                    product_name    TEXT    NOT NULL,
                    quantity_added  INTEGER NOT NULL,
                    cost_per_unit   REAL    NOT NULL,
                    restock_date    TEXT    NOT NULL DEFAULT (date('now'))
                );
            """)

    # ── Products ──────────────────────────────────────────────────────────────

    def add_product(self, p: Product) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO products
                   (name, sku, category, quantity, reorder_level, unit_cost, unit_price)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (p.name, p.sku, p.category, p.quantity,
                 p.reorder_level, p.unit_cost, p.unit_price),
            )
            return cur.lastrowid

    def update_product(self, p: Product) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE products
                   SET name=?, sku=?, category=?, quantity=?, reorder_level=?,
                       unit_cost=?, unit_price=?, updated_at=date('now')
                   WHERE id=?""",
                (p.name, p.sku, p.category, p.quantity,
                 p.reorder_level, p.unit_cost, p.unit_price, p.id),
            )

    def delete_product(self, product_id: int) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))

    def get_product(self, product_id: int) -> Optional[Product]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE id=?", (product_id,)
            ).fetchone()
        return _row_to_product(row) if row else None

    def get_all_products(self) -> List[Product]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM products ORDER BY name"
            ).fetchall()
        return [_row_to_product(r) for r in rows]

    def get_low_stock_products(self) -> List[Product]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE quantity <= reorder_level ORDER BY quantity ASC"
            ).fetchall()
        return [_row_to_product(r) for r in rows]

    def adjust_stock(self, product_id: int, delta: int) -> None:
        """Add or subtract from a product's quantity."""
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE products
                   SET quantity = MAX(0, quantity + ?), updated_at = date('now')
                   WHERE id=?""",
                (delta, product_id),
            )

    # ── Sales ─────────────────────────────────────────────────────────────────

    def record_sale(self, sale: Sale) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO sales
                   (product_id, product_name, quantity_sold, unit_cost, sale_price, sale_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sale.product_id, sale.product_name, sale.quantity_sold,
                 sale.unit_cost, sale.sale_price, sale.sale_date),
            )
            # Deduct sold quantity from stock
            conn.execute(
                """UPDATE products
                   SET quantity = MAX(0, quantity - ?), updated_at = date('now')
                   WHERE id=?""",
                (sale.quantity_sold, sale.product_id),
            )
            return cur.lastrowid

    def get_all_sales(self) -> List[Sale]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sales ORDER BY sale_date DESC, id DESC"
            ).fetchall()
        return [_row_to_sale(r) for r in rows]

    def get_sales_by_date_range(self, start: str, end: str) -> List[Sale]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date",
                (start, end),
            ).fetchall()
        return [_row_to_sale(r) for r in rows]

    def get_daily_sales_summary(self) -> List[Tuple[str, float, float]]:
        """Returns list of (date, total_revenue, total_profit) tuples."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT sale_date,
                          SUM(quantity_sold * sale_price) AS revenue,
                          SUM(quantity_sold * (sale_price - unit_cost)) AS profit
                   FROM sales
                   GROUP BY sale_date
                   ORDER BY sale_date"""
            ).fetchall()
        return [(r["sale_date"], r["revenue"], r["profit"]) for r in rows]

    def get_monthly_sales_summary(self) -> List[Tuple[str, float, float]]:
        """Returns list of (month YYYY-MM, total_revenue, total_profit) tuples."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT strftime('%Y-%m', sale_date) AS month,
                          SUM(quantity_sold * sale_price)              AS revenue,
                          SUM(quantity_sold * (sale_price - unit_cost)) AS profit
                   FROM sales
                   GROUP BY month
                   ORDER BY month"""
            ).fetchall()
        return [(r["month"], r["revenue"], r["profit"]) for r in rows]

    def get_top_products_by_revenue(self, limit: int = 5) -> List[Tuple[str, float]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT product_name,
                          SUM(quantity_sold * sale_price) AS revenue
                   FROM sales
                   GROUP BY product_name
                   ORDER BY revenue DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        return [(r["product_name"], r["revenue"]) for r in rows]

    # ── Restock Records ───────────────────────────────────────────────────────

    def record_restock(self, r: RestockRecord) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                """INSERT INTO restock_records
                   (product_id, product_name, quantity_added, cost_per_unit, restock_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (r.product_id, r.product_name, r.quantity_added,
                 r.cost_per_unit, r.restock_date),
            )
            conn.execute(
                """UPDATE products
                   SET quantity = quantity + ?, updated_at = date('now')
                   WHERE id=?""",
                (r.quantity_added, r.product_id),
            )
            return cur.lastrowid

    def get_all_restock_records(self) -> List[RestockRecord]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM restock_records ORDER BY restock_date DESC, id DESC"
            ).fetchall()
        return [_row_to_restock(r) for r in rows]

    # ── Summary Stats ─────────────────────────────────────────────────────────

    def get_summary_stats(self) -> dict:
        with self._get_conn() as conn:
            total_products = conn.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]
            inventory_value = conn.execute(
                "SELECT COALESCE(SUM(quantity * unit_cost), 0) FROM products"
            ).fetchone()[0]
            total_revenue = conn.execute(
                "SELECT COALESCE(SUM(quantity_sold * sale_price), 0) FROM sales"
            ).fetchone()[0]
            total_profit = conn.execute(
                "SELECT COALESCE(SUM(quantity_sold * (sale_price - unit_cost)), 0) FROM sales"
            ).fetchone()[0]
            low_stock_count = conn.execute(
                "SELECT COUNT(*) FROM products WHERE quantity <= reorder_level"
            ).fetchone()[0]
            out_of_stock_count = conn.execute(
                "SELECT COUNT(*) FROM products WHERE quantity = 0"
            ).fetchone()[0]
        return {
            "total_products": total_products,
            "inventory_value": inventory_value,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
        }


# ── Row converters ─────────────────────────────────────────────────────────────

def _row_to_product(row: sqlite3.Row) -> Product:
    return Product(
        id=row["id"],
        name=row["name"],
        sku=row["sku"],
        category=row["category"],
        quantity=row["quantity"],
        reorder_level=row["reorder_level"],
        unit_cost=row["unit_cost"],
        unit_price=row["unit_price"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_sale(row: sqlite3.Row) -> Sale:
    return Sale(
        id=row["id"],
        product_id=row["product_id"],
        product_name=row["product_name"],
        quantity_sold=row["quantity_sold"],
        unit_cost=row["unit_cost"],
        sale_price=row["sale_price"],
        sale_date=row["sale_date"],
    )


def _row_to_restock(row: sqlite3.Row) -> RestockRecord:
    return RestockRecord(
        id=row["id"],
        product_id=row["product_id"],
        product_name=row["product_name"],
        quantity_added=row["quantity_added"],
        cost_per_unit=row["cost_per_unit"],
        restock_date=row["restock_date"],
    )
