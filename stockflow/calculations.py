"""
Business logic: profit calculations, trend analysis, restock recommendations.
"""
from typing import List, Tuple, Optional
from stockflow.models import Product, Sale


# Profit calculations

def calc_gross_profit(revenue: float, cogs: float) -> float:
    """Revenue minus cost of goods sold."""
    return revenue - cogs


def calc_profit_margin_pct(revenue: float, cogs: float) -> float:
    """Gross profit margin as a percentage (0-100)."""
    if revenue == 0:
        return 0.0
    return ((revenue - cogs) / revenue) * 100


def calc_markup_pct(unit_cost: float, unit_price: float) -> float:
    """Markup percentage over cost."""
    if unit_cost == 0:
        return 0.0
    return ((unit_price - unit_cost) / unit_cost) * 100


def calc_inventory_value(products: List[Product]) -> float:
    """Total stock value at cost across all products."""
    return sum(p.inventory_value for p in products)


def calc_potential_revenue(products: List[Product]) -> float:
    """Potential revenue if all current stock is sold at listed price."""
    return sum(p.potential_revenue for p in products)


def calc_cogs_from_sales(sales: List[Sale]) -> float:
    """Total cost of goods sold from a list of sales."""
    return sum(s.total_cost for s in sales)


def calc_total_revenue_from_sales(sales: List[Sale]) -> float:
    """Total revenue from a list of sales."""
    return sum(s.total_revenue for s in sales)


# Trend analysis

def moving_average(values: List[float], window: int = 3) -> List[float]:
    """Simple moving average over a list of numeric values."""
    if not values or window <= 0:
        return []
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        segment = values[start: i + 1]
        result.append(sum(segment) / len(segment))
    return result


def compute_growth_rate(current: float, previous: float) -> Optional[float]:
    """Period-over-period growth rate as a percentage.

    Returns None when the previous value is zero to avoid division by zero.
    """
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def summarize_trend(daily_data: List[Tuple[str, float, float]]) -> dict:
    """Summarise trend data from Database.get_daily_sales_summary.

    Parameters
    ----------
    daily_data:
        List of (date_str, revenue, profit) tuples in chronological order.

    Returns
    -------
    dict with keys: total_revenue, total_profit, avg_daily_revenue,
    avg_daily_profit, best_day, worst_day, overall_margin_pct.
    """
    if not daily_data:
        return {
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "avg_daily_revenue": 0.0,
            "avg_daily_profit": 0.0,
            "best_day": None,
            "worst_day": None,
            "overall_margin_pct": 0.0,
        }

    revenues = [r for _, r, _ in daily_data]
    profits = [p for _, _, p in daily_data]
    dates = [d for d, _, _ in daily_data]

    total_revenue = sum(revenues)
    total_profit = sum(profits)
    n = len(daily_data)

    best_idx = revenues.index(max(revenues))
    worst_idx = revenues.index(min(revenues))

    return {
        "total_revenue": total_revenue,
        "total_profit": total_profit,
        "avg_daily_revenue": total_revenue / n,
        "avg_daily_profit": total_profit / n,
        "best_day": dates[best_idx],
        "worst_day": dates[worst_idx],
        "overall_margin_pct": calc_profit_margin_pct(
            total_revenue,
            total_revenue - total_profit,
        ),
    }


# Restock recommendations

def restock_recommendations(products: List[Product]) -> List[dict]:
    """Return a list of restock recommendations for low-stock products.

    Each recommendation dict contains:
      - product_id, name, sku, current_qty, reorder_level, suggested_qty
    """
    recs = []
    for p in products:
        if p.is_low_stock:
            # Suggest restocking to 3x the reorder level, at minimum
            suggested = max(p.reorder_level * 3, 10)
            recs.append({
                "product_id": p.id,
                "name": p.name,
                "sku": p.sku,
                "current_qty": p.quantity,
                "reorder_level": p.reorder_level,
                "suggested_qty": suggested,
                "estimated_cost": suggested * p.unit_cost,
                "is_out_of_stock": p.is_out_of_stock,
            })
    # Sort: out-of-stock first, then by quantity ascending
    recs.sort(key=lambda r: (not r["is_out_of_stock"], r["current_qty"]))
    return recs
