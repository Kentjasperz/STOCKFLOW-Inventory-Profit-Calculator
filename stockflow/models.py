"""
Data models for STOCKFLOW.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Product:
    """Represents an inventory product."""
    name: str
    sku: str
    category: str
    quantity: int
    reorder_level: int
    unit_cost: float
    unit_price: float
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def inventory_value(self) -> float:
        """Total value of current stock at cost."""
        return self.quantity * self.unit_cost

    @property
    def potential_revenue(self) -> float:
        """Potential revenue if all stock is sold."""
        return self.quantity * self.unit_price

    @property
    def profit_margin_pct(self) -> float:
        """Per-unit profit margin as a percentage."""
        if self.unit_price == 0:
            return 0.0
        return ((self.unit_price - self.unit_cost) / self.unit_price) * 100

    @property
    def is_low_stock(self) -> bool:
        """True when quantity is at or below the reorder level."""
        return self.quantity <= self.reorder_level

    @property
    def is_out_of_stock(self) -> bool:
        """True when quantity is zero."""
        return self.quantity == 0


@dataclass
class Sale:
    """Represents a recorded sale transaction."""
    product_id: int
    product_name: str
    quantity_sold: int
    unit_cost: float
    sale_price: float
    sale_date: str
    id: Optional[int] = None

    @property
    def total_revenue(self) -> float:
        return self.quantity_sold * self.sale_price

    @property
    def total_cost(self) -> float:
        return self.quantity_sold * self.unit_cost

    @property
    def gross_profit(self) -> float:
        return self.total_revenue - self.total_cost

    @property
    def profit_margin_pct(self) -> float:
        if self.total_revenue == 0:
            return 0.0
        return (self.gross_profit / self.total_revenue) * 100


@dataclass
class RestockRecord:
    """Records a restocking event for a product."""
    product_id: int
    product_name: str
    quantity_added: int
    cost_per_unit: float
    restock_date: str
    id: Optional[int] = None

    @property
    def total_cost(self) -> float:
        return self.quantity_added * self.cost_per_unit
