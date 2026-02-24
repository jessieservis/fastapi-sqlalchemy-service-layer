"""
services/item_service.py -- Business logic layer for Items.

Rules enforced here:
- No two items may share the same name (case-insensitive).
- Bulk discounts are applied by price threshold.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from db.models import Item


def get_all_items(db: Session) -> List[Item]:
    return db.query(Item).all()


def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()


def create_item(db: Session, name: str, description: str, price: float) -> Item:
    """
    Create a new item.
    Raises ValueError if an item with the same name already exists.
    """
    existing = db.query(Item).filter(Item.name.ilike(name)).first()
    if existing:
        raise ValueError(f"An item named '{name}' already exists.")

    db_item = Item(name=name, description=description, price=price)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(
    db: Session,
    item_id: int,
    name: str,
    description: str,
    price: float,
) -> Optional[Item]:
    """
    Update an existing item by id.
    Returns None if the item does not exist.
    """
    db_item = get_item_by_id(db, item_id)
    if db_item is None:
        return None

    db_item.name = name
    db_item.description = description
    db_item.price = price

    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, item_id: int) -> bool:
    """
    Delete an item by id.
    Returns True if deleted, False if not found.
    """
    db_item = get_item_by_id(db, item_id)
    if db_item is None:
        return False

    db.delete(db_item)
    db.commit()
    return True


def apply_bulk_discount(
    db: Session,
    threshold: float,
    discount_pct: float,
) -> int:
    """
    Reduce the price of every item whose price > threshold
    by discount_pct percent (e.g. 10.0 means 10% off).
    Returns the number of items updated.
    """
    items = db.query(Item).filter(Item.price > threshold).all()
    for item in items:
        item.price = round(item.price * (1 - discount_pct / 100), 2)
    db.commit()
    return len(items)


def search_items_by_name(db: Session, query: str) -> List[Item]:
    """Return all items whose name contains query (case-insensitive)."""
    return db.query(Item).filter(Item.name.ilike(f"%{query}%")).all()
