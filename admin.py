"""Admin data operations; UI also enforces role checks."""
from database import query,get_db
from products import create_product

def metrics():
    return {'sales':query("SELECT COALESCE(SUM(total),0) n FROM orders WHERE payment_status IN ('Paid','COD')",one=True)['n'],
      'orders':query('SELECT COUNT(*) n FROM orders',one=True)['n'],
      'customers':query("SELECT COUNT(*) n FROM users WHERE role='customer'",one=True)['n'],
      'products':query('SELECT COUNT(*) n FROM products WHERE is_active=1',one=True)['n']}

def all_orders(): return query('SELECT o.*,u.name customer,u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC')
def set_order_status(order_id,status):
    allowed=['Order Placed','Payment Confirmed','Processing','Packed','Shipped','Out for Delivery','Delivered','Cancelled']
    if status not in allowed: raise ValueError('Invalid order status.')
    with get_db() as db: db.execute('UPDATE orders SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(status,order_id))

def set_product_active(product_id,active):
    with get_db() as db: db.execute('UPDATE products SET is_active=? WHERE id=?',(int(active),product_id))

def create_coupon(code,percent,min_order,max_discount):
    with get_db() as db: db.execute('INSERT INTO coupons(code,discount_percent,min_order,max_discount) VALUES(?,?,?,?)',(code.upper(),percent,min_order,max_discount))
