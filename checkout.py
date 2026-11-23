"""Order placement and payment state transitions."""
import json,secrets
from database import get_db,query
from cart import cart_items
from config import DELIVERY_FEE,FREE_DELIVERY_OVER
from payments import create_razorpay_order,verify_checkout_signature,fetch_payment

STATUSES=['Order Placed','Payment Confirmed','Processing','Packed','Shipped','Out for Delivery','Delivered']

def totals(items,coupon=None):
    subtotal=sum(i['price']*i['quantity'] for i in items)
    discount=0
    if coupon:
        c=query('SELECT * FROM coupons WHERE code=? AND is_active=1',(coupon.upper(),),one=True)
        if c and subtotal>=c['min_order'] and (not c['usage_limit'] or c['used_count']<c['usage_limit']):
            discount=min(subtotal*c['discount_percent']//100,c['max_discount'])
    delivery=0 if subtotal-discount>=FREE_DELIVERY_OVER else DELIVERY_FEE
    return subtotal,discount,delivery,subtotal-discount+delivery

def create_order(user_id,shipping,payment_method,coupon=None):
    items=cart_items(user_id)
    if not items: raise ValueError('Your bag is empty.')
    for i in items:
        if i['quantity']>i['stock']: raise ValueError(f"Insufficient stock for {i['name']}.")
    subtotal,discount,delivery,total=totals(items,coupon)
    number='ASQ-'+secrets.token_hex(4).upper()
    with get_db() as db:
        cur=db.execute("INSERT INTO orders(order_number,user_id,subtotal,discount,delivery_fee,total,payment_method,payment_status,coupon_code,shipping_json) VALUES(?,?,?,?,?,?,?,?,?,?)",(number,user_id,subtotal,discount,delivery,total,payment_method,'Pending' if payment_method=='Razorpay' else 'COD',coupon.upper() if coupon else None,json.dumps(shipping)))
        oid=cur.lastrowid
        for i in items:
            db.execute('INSERT INTO order_items(order_id,product_id,variant_id,product_name,sku,size,colour,unit_price,quantity) VALUES(?,?,?,?,?,?,?,?,?)',
              (oid,i['product_id'],i['variant_id'],i['name'],f"ASQ-{i['product_id']}",i['size'],i['colour'],i['price'],i['quantity']))
            changed=db.execute('UPDATE product_variants SET stock=stock-? WHERE id=? AND stock>=?',(i['quantity'],i['variant_id'],i['quantity']))
            if changed.rowcount != 1:
                raise ValueError(f"Insufficient stock for {i['name']}; refresh your bag and try again.")
        db.execute('DELETE FROM cart_items WHERE cart_id=(SELECT id FROM carts WHERE user_id=?)',(user_id,))
        if coupon: db.execute('UPDATE coupons SET used_count=used_count+1 WHERE code=?',(coupon.upper(),))
    order={'id':oid,'order_number':number,'total':total}
    if payment_method=='Razorpay':
        try:
            rp=create_razorpay_order(total*100,number)
            with get_db() as db:
                db.execute('INSERT INTO payments(order_id,provider,provider_order_id,amount,status,raw_json) VALUES(?,?,?,?,?,?)',(oid,'razorpay',rp['id'],total,'created',json.dumps(rp)))
            order['razorpay_order']=rp
        except Exception:
            # Keep order and reserved inventory visible for admin reconciliation; do not fake a payment.
            raise
    else:
        with get_db() as db: db.execute('INSERT INTO payments(order_id,provider,amount,status) VALUES(?,?,?,?)',(oid,'cod',total,'pending'))
    return order

def confirm_razorpay(order_id,payment_id,signature):
    payment=query('SELECT * FROM payments WHERE provider_order_id=?',(order_id,),one=True)
    if not payment: raise ValueError('Payment order not found.')
    if payment['status']=='captured': return True
    if not verify_checkout_signature(order_id,payment_id,signature): raise ValueError('Payment signature verification failed.')
    remote=fetch_payment(payment_id)
    if remote.get('order_id')!=order_id or remote.get('status')!='captured' or remote.get('amount')!=payment['amount']*100:
        raise ValueError('Payment is not captured or amount does not match.')
    with get_db() as db:
        db.execute("UPDATE payments SET provider_payment_id=?,status='captured',signature=?,raw_json=? WHERE id=?",(payment_id,signature,json.dumps(remote),payment['id']))
        db.execute("UPDATE orders SET payment_status='Paid',status='Payment Confirmed',updated_at=CURRENT_TIMESTAMP WHERE id=?",(payment['order_id'],))
    return True

def user_orders(user_id): return query('SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC',(user_id,))
def order_items(order_id): return query('SELECT * FROM order_items WHERE order_id=?',(order_id,))
