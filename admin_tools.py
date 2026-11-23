"""Admin helpers: picture upload (multiple) and product editing.

Table names are discovered at runtime, so this works with your existing database.
Uploaded pictures are resized, compressed and stored as data URIs in the database,
so they work in product cards and product pages with no extra server setup.
"""
import io, base64
from PIL import Image
from database import query, get_db


# ---------------------------------------------------------------- pictures
def file_to_data_uri(f, max_side=800, quality=78):
    img = Image.open(f)
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGBA')
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    else:
        img = img.convert('RGB')
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=quality, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- db helpers
def _write(sql, params=()):
    with get_db() as db:
        cur = db.execute(sql, params)
        return cur.lastrowid


def _cols(table):
    return [c['name'] for c in query(f'PRAGMA table_info({table})')]


def _find(required):
    for t in query("SELECT name FROM sqlite_master WHERE type='table'"):
        n = t['name']
        if n.startswith('sqlite_'):
            continue
        c = _cols(n)
        if all(r in c for r in required):
            return n, c
    return None, []


def _img_table():
    n, c = _find(['product_id', 'image_url'])
    if n:
        return n, c
    _write('CREATE TABLE IF NOT EXISTS product_images('
           'id INTEGER PRIMARY KEY AUTOINCREMENT,product_id INTEGER NOT NULL,'
           'image_url TEXT NOT NULL,sort_order INTEGER DEFAULT 0)')
    return 'product_images', ['id', 'product_id', 'image_url', 'sort_order']


def _var_table():
    n, c = _find(['product_id', 'size', 'colour', 'stock'])
    if not n:
        raise RuntimeError('Could not find the product variants table.')
    return n, c


# ---------------------------------------------------------------- gallery
def product_images(pid):
    t, _ = _img_table()
    return [dict(r) for r in query(
        f'SELECT rowid AS id,image_url FROM {t} WHERE product_id=? ORDER BY rowid', (pid,))]


def add_images(pid, urls):
    t, cols = _img_table()
    start = len(product_images(pid))
    for i, u in enumerate(urls):
        if 'sort_order' in cols:
            _write(f'INSERT INTO {t}(product_id,image_url,sort_order) VALUES(?,?,?)', (pid, u, start + i))
        else:
            _write(f'INSERT INTO {t}(product_id,image_url) VALUES(?,?)', (pid, u))


def remove_images(ids):
    t, _ = _img_table()
    for i in ids:
        _write(f'DELETE FROM {t} WHERE rowid=?', (i,))


# ---------------------------------------------------------------- product
def update_product(pid, **fields):
    allowed = set(_cols('products'))
    items = [(k, v) for k, v in fields.items() if k in allowed]
    if not items:
        return
    sets = ','.join(f'{k}=?' for k, _ in items)
    _write(f'UPDATE products SET {sets} WHERE id=?', tuple(v for _, v in items) + (pid,))


# ---------------------------------------------------------------- variants
def variants_for(pid):
    t, _ = _var_table()
    return [dict(r) for r in query(
        f'SELECT rowid AS id,size,colour,stock FROM {t} WHERE product_id=? ORDER BY rowid', (pid,))]


def update_variant(vid, size, colour, stock):
    t, _ = _var_table()
    _write(f'UPDATE {t} SET size=?,colour=?,stock=? WHERE rowid=?', (size, colour, int(stock), vid))


def add_variant(pid, size, colour, stock):
    t, _ = _var_table()
    _write(f'INSERT INTO {t}(product_id,size,colour,stock) VALUES(?,?,?,?)', (pid, size, colour, int(stock)))
