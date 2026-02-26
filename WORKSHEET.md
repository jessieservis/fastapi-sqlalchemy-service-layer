# Worksheet: FastAPI + SQLAlchemy Service Layer

**CPS 420:** Web Application Development–Web Services SOA

**Time:** 75 minutes  

**Repo:** `git clone https://github.com/Cnets-io/fastapi-sqlalchemy-service-layer.git`

**Assignment:** Clone this repository and submit to your own new Git repository.

---

## Learning Objectives

By the end of this lab you will be able to:

1. Explain the purpose of a **service layer** and how it differs from direct database access.
2. Implement CRUD operations inside `services/item_service.py`.
3. Wire service functions to FastAPI route handlers in `app.py`.
4. Render results using Jinja2 templates.

---

## Background

This project separates concerns into three layers:

| Layer | Folder / File | Responsibility |
|-------|--------------|----------------|
| **Database** | `db/` | SQLAlchemy engine, session, and ORM model |
| **Service** | `services/` | Business logic; all DB queries live here |
| **Presentation** | `app.py` + `templates/` | HTTP routes and HTML rendering |

The `app.py` file should **never** import `Session` or query the database directly.
All database work is delegated to the service layer.

---

## Project Structure

```
fastapi-sqlalchemy-service-layer/
|-- app.py                  # FastAPI routes (presentation layer)
|-- requirements.txt
|-- db/
|   |-- __init__.py
|   |-- database.py         # Engine + get_db dependency
|   `-- models.py           # Item ORM model
|-- services/
|   |-- __init__.py
|   `-- item_service.py     # <-- YOU WILL COMPLETE THIS
`-- templates/
    |-- base.html
    |-- index.html
    `-- create_item.html
```

---

## Setup (5 minutes)

```bash
# 1. Clone the repository and create a new one that is no longer linked
git clone https://github.com/Cnets-io/fastapi-sqlalchemy-service-layer.git
cd fastapi-sqlalchemy-service-layer
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPO.git
git branch -M main
git push -u origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
uvicorn app:app --reload

# 4. Open your browser
#    http://127.0.0.1:8000/items/ui
```

The app will start but most routes will return errors until you complete the exercises below.

---

## Part 1 - Explore the Existing Code (10 minutes)

Open each file and answer the questions in your own words.

### 1a. `db/models.py`

- What table name does the `Item` model map to?
- List every column and its Python type.
- Which column has a default value? What is it?

```
Your answer:
- What table name does the `Item` model map to?
    the 'items' table
- List every column and its Python type.
    id: int
    name: String
    description: String
    price: float
- Which column has a default value? What is it?
    description has a defualt value of ""
```

### 1b. `db/database.py`

- What SQLAlchemy function creates the engine?
- What does `get_db` do, and why does it use `yield`?

```
Your answer:
- What SQLAlchemy function creates the engine?
    create_engine
- What does `get_db` do, and why does it use `yield`?
    get_db is a generator function and can pause and resume at any point. It uses yield key word to do that.
```

### 1c. `app.py`

- How does the `@app.on_event("startup")` handler differ from the older `@app.on_event` pattern?  
  *(Hint: look at the lifespan context manager.)*
- How does `app.py` receive a database session without importing `Session` directly?

```
Your answer:
- How does the `@app.on_event("startup")` handler differ from the older `@app.on_event` pattern?  
  *(Hint: look at the lifespan context manager.)*
    The lifespan context manager combines both startup and shutdown functionalities for the app.
- How does `app.py` receive a database session without importing `Session` directly?
    It receives it throught the get_db function
```

---

## Part 2 - Implement the Service Layer (40 minutes)

Open `services/item_service.py`. You will find stub functions with `TODO` comments.
Implement each function. **Do not modify `app.py` or any file in `db/`.**

### Exercise 2.1 - `get_all_items`

Return a list of all `Item` rows from the database.

```python
def get_all_items(db: Session) -> List[Item]:
    return db.query(Item).all()
```

**Test:** Navigate to `http://127.0.0.1:8000/items/ui` — you should see an empty table (no error).

---

### Exercise 2.2 - `get_item_by_id`

Return a single `Item` by primary key, or `None` if not found.

```python
def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.id == item_id).first()
```

---

### Exercise 2.3 - `create_item`

Create and persist a new `Item`. Return the saved object.

```python
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
```

**Test:** Use the form at `http://127.0.0.1:8000/items/ui/new` to create an item.

---

### Exercise 2.4 - `delete_item`

Delete an item by ID. Return `True` if deleted, `False` if not found.

```python
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
```

**Test:** Use the Delete button next to any item in the list.

---

### Exercise 2.5 - `apply_discount` (Challenge)

Reduce the price of every item by `percent` percent (e.g., 10 means 10% off).
Return the number of items updated.

```python
def apply_discount(
    db: Session,
    discount_pct: float,
):
    """
    Reduce the price of every item whose price > threshold
    by discount_pct percent (e.g. 10.0 means 10% off).
    Returns the number of items updated.
    """
    items = db.query(Item).all()
    for item in items:
        item.price = round(item.price * (1 - discount_pct / 100), 2)
    db.commit()
    return len(items)
```

**Test:** `POST /items/discount?percent=10` (use the FastAPI docs at `/docs`).

---

## Part 3 - Verify with the API (10 minutes)

Open `http://127.0.0.1:8000/docs` (Swagger UI) and test each endpoint:

| Endpoint | Expected Result |
|----------|-----------------|
| `GET /items` | JSON list of all items |
| `GET /items/{id}` | Single item JSON or 404 |
| `POST /items` | New item created |
| `DELETE /items/{id}` | Item removed |
| `POST /items/discount?percent=10` | Prices reduced by 10% |

For each endpoint, record the HTTP status code you received:

```
GET /items          status: 200
GET /items/1        status: 200
POST /items         status: 201
DELETE /items/1     status: 200
POST /items/discount status: 200
```

---

## Part 4 - Reflection Questions (10 minutes)

Answer in 2-3 sentences each.

1. **Why is it better to keep database queries out of `app.py`?**

```
Your answer:
    It is better to keep database queries out of app.py for many reasons. One many reason is for testing. Having db queries in their own file allows for those tests to be unit tests, rather than integration tests. In addition, it is better for reusability. Not all db calls may come from app.py, so you don't want to have to rewrite code.
```

2. **What would you need to change if you switched from SQLite to PostgreSQL?**

```
Your answer:
    SQLite works from a database file, as seen in this project as app.db. Other SQL versions, such as PostgreSQL work from servers. So, I would need to chance the database url to a PostgreSQL, which would likely have a login within it. I would also need to add checks for the db server to make sure the connection was successfully.
```

3. **How does Jinja2 template inheritance (base.html) reduce code duplication?**

```
Your answer: 
    base.html acts as a template that is passed to other html pages. Each html page that inherits the template only has to define what is different. That way, you don't have to recode the app headers and other shared details.
```

4. **What does `db.refresh(item)` do after `db.commit()`?**

```
Your answer:
    db.refresh(item) is a function that updates the objects state from the database. The db.commit() updated/added an item, so it refreshed the table row so the object is updated. It makes sure the app is looking at the most recent version of the data.
```

---

## Submission Checklist

- [x] `services/item_service.py` — all five functions implemented
- [x] UI at `/items/ui` displays items with no errors
- [x] Items can be created via the form
- [x] Items can be deleted via the Delete button
- [x] `/items/discount` reduces prices correctly
- [x] All reflection questions answered

---

## Solution Reference

Solutions are available in the repository comments. Try to complete the exercises **before** reading them.

```python
# Exercise 2.1
def get_all_items(db: Session) -> list[Item]:
    return db.query(Item).all()

# Exercise 2.2
def get_item_by_id(db: Session, item_id: int) -> Item | None:
    return db.query(Item).filter(Item.id == item_id).first()

# Exercise 2.3
def create_item(db: Session, name: str, description: str, price: float) -> Item:
    item = Item(name=name, description=description, price=price)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# Exercise 2.4
def delete_item(db: Session, item_id: int) -> bool:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True

# Exercise 2.5
def apply_discount(db: Session, percent: float) -> int:
    items = db.query(Item).all()
    for item in items:
        item.price = round(item.price * (1 - percent / 100), 2)
    db.commit()
    return len(items)
```
