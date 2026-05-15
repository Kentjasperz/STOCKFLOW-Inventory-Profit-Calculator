"""Tests for stockflow.database module."""
import pytest
import os
from stockflow.database import Database
from stockflow.models import Product, Sale, RestockRecord


@pytest.fixture
def db(tmp_path):
    return Database(db_path=str(tmp_path / "test.db"))


def make_product(**kwargs):
    defaults = dict(name="Widget", sku="W001", category="General",
                    quantity=10, reorder_level=5, unit_cost=5.0, unit_price=10.0)
    defaults.update(kwargs)
    return Product(**defaults)


def test_add_and_get_product(db):
    pid = db.add_product(make_product())
    p = db.get_product(pid)
    assert p.name == "Widget"
    assert p.quantity == 10


def test_update_product(db):
    pid = db.add_product(make_product())
    p = db.get_product(pid)
    p.quantity = 99
    db.update_product(p)
    assert db.get_product(pid).quantity == 99


def test_delete_product(db):
    pid = db.add_product(make_product())
    db.delete_product(pid)
    assert db.get_product(pid) is None


def test_get_low_stock(db):
    db.add_product(make_product(sku="A", quantity=3, reorder_level=5))
    db.add_product(make_product(sku="B", quantity=20, reorder_level=5))
    low = db.get_low_stock_products()
    assert len(low) == 1
    assert low[0].sku == "A"


def test_record_sale_deducts_stock(db):
    pid = db.add_product(make_product(quantity=10))
    sale = Sale(product_id=pid, product_name="Widget", quantity_sold=3,
                unit_cost=5.0, sale_price=10.0, sale_date="2024-01-01")
    db.record_sale(sale)
    assert db.get_product(pid).quantity == 7


def test_record_restock_adds_stock(db):
    pid = db.add_product(make_product(quantity=5))
    r = RestockRecord(product_id=pid, product_name="Widget",
                      quantity_added=10, cost_per_unit=5.0,
                      restock_date="2024-01-01")
    db.record_restock(r)
    assert db.get_product(pid).quantity == 15


def test_summary_stats(db):
    pid = db.add_product(make_product(quantity=10))
    sale = Sale(product_id=pid, product_name="Widget", quantity_sold=2,
                unit_cost=5.0, sale_price=10.0, sale_date="2024-01-01")
    db.record_sale(sale)
    stats = db.get_summary_stats()
    assert stats["total_revenue"] == pytest.approx(20.0)
    assert stats["total_profit"] == pytest.approx(10.0)
