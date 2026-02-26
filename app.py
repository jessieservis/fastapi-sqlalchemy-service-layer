"""
app.py -- FastAPI routes + Pydantic schemas.

Layers:
  app.py          <- HTTP in/out, Pydantic validation
  services/       <- business logic
  db/             <- database engine, session, ORM models
"""

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import engine, Base, get_db
import services.item_service as item_service


# ─────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=500)
    price: float = Field(..., gt=0)


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float


# ─────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    import db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("Database initialized")
    yield
    print("App shutting down")


app = FastAPI(
    title="FastAPI + SQLAlchemy + Service Layer",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────────────────────────
# HTML UI routes
# ─────────────────────────────────────────────────────────────

@app.get("/items/ui", response_class=HTMLResponse)
async def items_page(request: Request, db: Session = Depends(get_db)):
    items = item_service.get_all_items(db)
    return templates.TemplateResponse(
        "items_list.html",
        {"request": request, "items": items},
    )

@app.get("/items/ui/new", response_class=HTMLResponse)
async def create_item_form(request: Request):
    return templates.TemplateResponse(
        "create_item.html",
        {"request": request},
    )


@app.post("/items/ui")
async def create_item_from_form(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    db: Session = Depends(get_db),
):
    try:
        item_service.create_item(db, name=name, description=description, price=price)
    except ValueError:
        pass
    return RedirectResponse(url="/items/ui", status_code=303)


@app.get("/items/ui/{item_id}", response_class=HTMLResponse)
async def item_detail(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = item_service.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return templates.TemplateResponse(
        "item_detail.html",
        {"request": request, "item": item},
    )


@app.post("/items/ui/{item_id}/delete")
async def delete_item_from_ui(item_id: int, db: Session = Depends(get_db)):
    item_service.delete_item(db, item_id)
    return RedirectResponse(url="/items/ui", status_code=303)

# ─────────────────────────────────────────────────────────────
# JSON API routes
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "message": "FastAPI + SQLAlchemy + Service Layer"}


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    try:
        return item_service.create_item(
            db,
            name=item.name,
            description=item.description,
            price=item.price,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/items/search", response_model=List[ItemResponse])
def search_items(q: str, db: Session = Depends(get_db)):
    return item_service.search_items_by_name(db, q)


@app.get("/items", response_model=List[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    return item_service.get_all_items(db)


@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = item_service.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    updated = item_service.update_item(
        db, item_id,
        name=item.name,
        description=item.description,
        price=item.price,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    deleted = item_service.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item deleted"}

@app.post("/items/discount")
def apply_discount(discount_pct: float, db: Session = Depends(get_db)):
    count = item_service.apply_discount(db, discount_pct)
    return {"detail": f"{count} item(s) discounted by {discount_pct}%" , "updated": count}

# @app.post("/items/discount")
# def bulk_discount(threshold: float, discount_pct: float, db: Session = Depends(get_db)):
#     count = item_service.apply_bulk_discount(db, threshold, discount_pct)
#     return {"detail": f"{count} item(s) discounted by {discount_pct}%", "updated": count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
