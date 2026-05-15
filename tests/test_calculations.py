"""
Tests for stockflow.calculations module.
"""
import pytest
from stockflow.calculations import (
    calc_gross_profit,
    calc_profit_margin_pct,
    calc_markup_pct,
    calc_inventory_value,
    calc_potential_revenue,
    calc_cogs_from_sales,
    calc_total_revenue_from_sales,
    moving_average,
    compute_growth_rate,
    summarize_trend,
    restock_recommendations,
)
from stockflow.models import Product, Sale


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_product(name="Widget", quantity=10, reorder_level=5,
                 unit_cost=5.0, unit_price=10.0, sku="W001", id=1):
    return Product(
        id=id, name=name, sku=sku, category="Test",
        quantity=quantity, reorder_level=reorder_level,
        unit_cost=unit_cost, unit_price=unit_price,
    )


def make_sale(qty=2, unit_cost=5.0, sale_price=10.0):
    return Sale(
        id=1, product_id=1, product_name="Widget",
        quantity_sold=qty, unit_cost=unit_cost,
        sale_price=sale_price, sale_date="2024-01-01",
    )


# ── calc_gross_profit ──────────────────────────────────────────────────────────

def test_gross_profit_positive():
    assert calc_gross_profit(200.0, 120.0) == pytest.approx(80.0)


def test_gross_profit_zero_cost():
    assert calc_gross_profit(100.0, 0.0) == pytest.approx(100.0)


def test_gross_profit_negative_when_cost_exceeds_revenue():
    assert calc_gross_profit(50.0, 80.0) == pytest.approx(-30.0)


# ── calc_profit_margin_pct ─────────────────────────────────────────────────────

def test_margin_standard():
    assert calc_profit_margin_pct(200.0, 100.0) == pytest.approx(50.0)


def test_margin_zero_revenue():
    assert calc_profit_margin_pct(0.0, 50.0) == pytest.approx(0.0)


def test_margin_full_profit():
    assert calc_profit_margin_pct(100.0, 0.0) == pytest.approx(100.0)


def test_margin_negative_when_cogs_exceeds_revenue():
    result = calc_profit_margin_pct(80.0, 100.0)
    assert result < 0


# ── calc_markup_pct ────────────────────────────────────────────────────────────

def test_markup_standard():
    assert calc_markup_pct(5.0, 10.0) == pytest.approx(100.0)


def test_markup_zero_cost():
    assert calc_markup_pct(0.0, 10.0) == pytest.approx(0.0)


def test_markup_no_markup():
    assert calc_markup_pct(10.0, 10.0) == pytest.approx(0.0)


# ── Product model properties ───────────────────────────────────────────────────

def test_product_inventory_value():
    p = make_product(quantity=10, unit_cost=3.0)
    assert p.inventory_value == pytest.approx(30.0)


def test_product_potential_revenue():
    p = make_product(quantity=10, unit_price=8.0)
    assert p.potential_revenue == pytest.approx(80.0)


def test_product_profit_margin():
    p = make_product(unit_cost=4.0, unit_price=10.0)
    assert p.profit_margin_pct == pytest.approx(60.0)


def test_product_is_low_stock_true():
    p = make_product(quantity=3, reorder_level=5)
    assert p.is_low_stock is True


def test_product_is_low_stock_at_boundary():
    p = make_product(quantity=5, reorder_level=5)
    assert p.is_low_stock is True


def test_product_is_low_stock_false():
    p = make_product(quantity=6, reorder_level=5)
    assert p.is_low_stock is False


def test_product_is_out_of_stock():
    p = make_product(quantity=0)
    assert p.is_out_of_stock is True


def test_product_not_out_of_stock():
    p = make_product(quantity=1)
    assert p.is_out_of_stock is False


# ── calc_inventory_value ───────────────────────────────────────────────────────

def test_calc_inventory_value_multiple():
    products = [make_product(quantity=10, unit_cost=2.0, id=1, sku="A"),
                make_product(quantity=5, unit_cost=4.0, id=2, sku="B")]
    assert calc_inventory_value(products) == pytest.approx(40.0)


def test_calc_inventory_value_empty():
    assert calc_inventory_value([]) == pytest.approx(0.0)


# ── Sale model properties ──────────────────────────────────────────────────────

def test_sale_total_revenue():
    s = make_sale(qty=3, sale_price=12.0)
    assert s.total_revenue == pytest.approx(36.0)


def test_sale_total_cost():
    s = make_sale(qty=3, unit_cost=5.0)
    assert s.total_cost == pytest.approx(15.0)


def test_sale_gross_profit():
    s = make_sale(qty=3, unit_cost=5.0, sale_price=12.0)
    assert s.gross_profit == pytest.approx(21.0)


def test_sale_margin():
    s = make_sale(qty=1, unit_cost=5.0, sale_price=10.0)
    assert s.profit_margin_pct == pytest.approx(50.0)


# ── moving_average ─────────────────────────────────────────────────────────────

def test_moving_average_basic():
    result = moving_average([1.0, 2.0, 3.0, 4.0, 5.0], window=3)
    assert result[2] == pytest.approx(2.0)
    assert result[4] == pytest.approx(4.0)


def test_moving_average_window_1():
    values = [10.0, 20.0, 30.0]
    assert moving_average(values, window=1) == pytest.approx(values)


def test_moving_average_empty():
    assert moving_average([], window=3) == []


def test_moving_average_window_larger_than_data():
    result = moving_average([5.0, 10.0], window=5)
    assert len(result) == 2


# ── compute_growth_rate ────────────────────────────────────────────────────────

def test_growth_rate_positive():
    assert compute_growth_rate(110.0, 100.0) == pytest.approx(10.0)


def test_growth_rate_negative():
    assert compute_growth_rate(90.0, 100.0) == pytest.approx(-10.0)


def test_growth_rate_zero_previous():
    assert compute_growth_rate(50.0, 0.0) is None


# ── summarize_trend ────────────────────────────────────────────────────────────

def test_summarize_trend_empty():
    result = summarize_trend([])
    assert result["total_revenue"] == 0.0
    assert result["best_day"] is None


def test_summarize_trend_single_day():
    data = [("2024-01-01", 100.0, 40.0)]
    result = summarize_trend(data)
    assert result["total_revenue"] == pytest.approx(100.0)
    assert result["total_profit"] == pytest.approx(40.0)
    assert result["overall_margin_pct"] == pytest.approx(40.0)
    assert result["best_day"] == "2024-01-01"
    assert result["worst_day"] == "2024-01-01"


def test_summarize_trend_multiple_days():
    data = [
        ("2024-01-01", 100.0, 30.0),
        ("2024-01-02", 200.0, 80.0),
        ("2024-01-03", 50.0, 10.0),
    ]
    result = summarize_trend(data)
    assert result["total_revenue"] == pytest.approx(350.0)
    assert result["best_day"] == "2024-01-02"
    assert result["worst_day"] == "2024-01-03"


# ── restock_recommendations ────────────────────────────────────────────────────

def test_restock_recommendations_no_low_stock():
    products = [make_product(quantity=20, reorder_level=5)]
    assert restock_recommendations(products) == []


def test_restock_recommendations_low_stock():
    p = make_product(quantity=3, reorder_level=5)
    recs = restock_recommendations([p])
    assert len(recs) == 1
    assert recs[0]["current_qty"] == 3
    assert recs[0]["suggested_qty"] >= 15  # 3x reorder_level


def test_restock_recommendations_out_of_stock_first():
    p_low = make_product(quantity=2, reorder_level=5, id=1, sku="A")
    p_oos = make_product(quantity=0, reorder_level=5, id=2, sku="B")
    recs = restock_recommendations([p_low, p_oos])
    assert recs[0]["is_out_of_stock"] is True


def test_restock_recommendations_estimated_cost():
    p = make_product(quantity=0, reorder_level=5, unit_cost=2.0)
    recs = restock_recommendations([p])
    assert recs[0]["estimated_cost"] == pytest.approx(
        recs[0]["suggested_qty"] * 2.0
    )
