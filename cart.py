"""Cart and wishlist operations."""
from database import query,get_db

def add_to_cart(user_id,variant_id,qty=1):
    with get_db() as db:
        variant=db.execute('SELECT stock FROM product_variants WHERE id=?',(variant_id,)).fetchone()
        if not variant or variant['stock']<qty: raise ValueError('Selected option is out of stock.')
        cart=db.execute('SELECT id FROM carts WHERE user_id=?',(user_id,)).fetchone()
        if not cart:
            cur=db.execute('INSERT INTO carts(user_id) VALUES(?)',(user_id,)); cart={'id':cur.lastrowid}
        item=db.execute('SELECT id,quantity FROM cart_items WHERE cart_id=? AND variant_id=?',(cart['id'],variant_id)).fetchone()
        new_qty=(item['quantity'] if item else 0)+qty
        if new_qty>variant['stock']: raise ValueError('Not enough stock for that quantity.')
        if item: db.execute('UPDATE cart_items SET quantity=? WHERE id=?',(new_qty,item['id']))
        else: db.execute('INSERT INTO cart_items(cart_id,variant_id,quantity) VALUES(?,?,?)',(cart['id'],variant_id,qty))

def cart_items(user_id):
    return query("SELECT ci.id cart_item_id,ci.quantity,v.id variant_id,v.size,v.colour,v.stock,p.id product_id,p.name,p.brand,p.price,p.mrp,p.image_url FROM cart_items ci JOIN carts c ON c.id=ci.cart_id JOIN product_variants v ON v.id=ci.variant_id JOIN products p ON p.id=v.product_id WHERE c.user_id=?",(user_id,))

def set_quantity(user_id,item_id,qty):
    if qty<1: return remove_item(user_id,item_id)
    with get_db() as db:
        row=db.execute("SELECT ci.id,v.stock FROM cart_items ci JOIN carts c ON c.id=ci.cart_id JOIN product_variants v ON v.id=ci.variant_id WHERE ci.id=? AND c.user_id=?",(item_id,user_id)).fetchone()
        if not row: raise ValueError('Cart item not found.')
        if qty>row['stock']: raise ValueError('Requested quantity exceeds available stock.')
        db.execute('UPDATE cart_items SET quantity=? WHERE id=?',(qty,item_id))

def remove_item(user_id,item_id):
    with get_db() as db: db.execute('DELETE FROM cart_items WHERE id IN (SELECT ci.id FROM cart_items ci JOIN carts c ON c.id=ci.cart_id WHERE ci.id=? AND c.user_id=?)',(item_id,user_id))

def toggle_wishlist(user_id,product_id):
    with get_db() as db:
        row=db.execute('SELECT id FROM wishlists WHERE user_id=? AND product_id=?',(user_id,product_id)).fetchone()
        if row: db.execute('DELETE FROM wishlists WHERE id=?',(row['id'],)); return False
        db.execute('INSERT INTO wishlists(user_id,product_id) VALUES(?,?)',(user_id,product_id)); return True

def wishlist(user_id):
    return query('SELECT p.* FROM wishlists w JOIN products p ON p.id=w.product_id WHERE w.user_id=?',(user_id,))
