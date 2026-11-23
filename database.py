"""SQLite data layer. SQL uses portable types to ease a later PostgreSQL move."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer','admin')),
 phone TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS categories (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, parent_id INTEGER REFERENCES categories(id), slug TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL, brand TEXT NOT NULL DEFAULT 'A SQUARE',
 description TEXT DEFAULT '', category_id INTEGER REFERENCES categories(id), price INTEGER NOT NULL CHECK(price>=0),
 mrp INTEGER NOT NULL CHECK(mrp>=price), rating REAL NOT NULL DEFAULT 4.5, rating_count INTEGER NOT NULL DEFAULT 0,
 image_url TEXT DEFAULT '', is_active INTEGER NOT NULL DEFAULT 1, is_new INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS product_variants (
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
 size TEXT NOT NULL, colour TEXT NOT NULL, stock INTEGER NOT NULL DEFAULT 0 CHECK(stock>=0), UNIQUE(product_id,size,colour)
);
CREATE TABLE IF NOT EXISTS product_images (
 id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
 image_url TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS carts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS cart_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
 variant_id INTEGER NOT NULL REFERENCES product_variants(id), quantity INTEGER NOT NULL CHECK(quantity>0), UNIQUE(cart_id,variant_id)
);
CREATE TABLE IF NOT EXISTS wishlists (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, UNIQUE(user_id,product_id)
);
CREATE TABLE IF NOT EXISTS addresses (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 name TEXT NOT NULL, phone TEXT NOT NULL, line1 TEXT NOT NULL, line2 TEXT DEFAULT '', city TEXT NOT NULL,
 state TEXT NOT NULL, pincode TEXT NOT NULL, is_default INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS coupons (
 id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL UNIQUE, discount_percent INTEGER NOT NULL,
 min_order INTEGER NOT NULL DEFAULT 0, max_discount INTEGER NOT NULL DEFAULT 1000,
 expires_at TEXT, usage_limit INTEGER, used_count INTEGER NOT NULL DEFAULT 0, is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT NOT NULL UNIQUE, user_id INTEGER NOT NULL REFERENCES users(id),
 status TEXT NOT NULL DEFAULT 'Order Placed', subtotal INTEGER NOT NULL, discount INTEGER NOT NULL DEFAULT 0,
 delivery_fee INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL, payment_method TEXT NOT NULL,
 payment_status TEXT NOT NULL DEFAULT 'Pending', coupon_code TEXT, shipping_json TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
 product_id INTEGER NOT NULL REFERENCES products(id), variant_id INTEGER REFERENCES product_variants(id),
 product_name TEXT NOT NULL, sku TEXT NOT NULL, size TEXT NOT NULL, colour TEXT NOT NULL,
 unit_price INTEGER NOT NULL, quantity INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id), provider TEXT NOT NULL,
 provider_order_id TEXT, provider_payment_id TEXT UNIQUE, amount INTEGER NOT NULL, status TEXT NOT NULL,
 signature TEXT, raw_json TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reviews (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id), product_id INTEGER NOT NULL REFERENCES products(id),
 rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), title TEXT DEFAULT '', body TEXT DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,product_id)
);
CREATE TABLE IF NOT EXISTS inventory_movements (
 id INTEGER PRIMARY KEY AUTOINCREMENT, variant_id INTEGER NOT NULL REFERENCES product_variants(id),
 change_qty INTEGER NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS returns (
 id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL REFERENCES orders(id), user_id INTEGER NOT NULL REFERENCES users(id),
 reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Requested', refund_amount INTEGER NOT NULL DEFAULT 0,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_status ON orders(status);
"""

@contextmanager
def get_db():
    path=Path(DB_PATH)
    if str(path) != ':memory:': path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(str(path), check_same_thread=False, timeout=20)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def init_db():
    with get_db() as db: db.executescript(SCHEMA)

def query(sql, params=(), one=False):
    with get_db() as db:
        cur=db.execute(sql, params)
        rows=cur.fetchall()
        return (dict(rows[0]) if rows else None) if one else [dict(r) for r in rows]

def execute(sql, params=()):
    with get_db() as db:
        cur=db.execute(sql, params)
        return cur.lastrowid
