"""Product catalogue, inventory and search operations."""
from database import query, get_db

def list_products(search='', category='', min_price=0, max_price=100000, sizes=None, colours=None, min_rating=0, sort='Recommended'):
    sql="""SELECT p.*, c.name category FROM products p LEFT JOIN categories c ON c.id=p.category_id
           WHERE p.is_active=1 AND p.price BETWEEN ? AND ?"""
    params=[int(min_price),int(max_price)]
    if search:
        sql+=' AND (p.name LIKE ? OR p.brand LIKE ? OR p.description LIKE ?)'; term=f'%{search}%'; params += [term,term,term]
    if category and category!='All':
        sql+=' AND (c.name=? OR c.parent_id=(SELECT id FROM categories WHERE name=?))'; params.extend([category,category])
    if min_rating: sql+=' AND p.rating>=?'; params.append(float(min_rating))
    order={'Newest arrivals':'p.created_at DESC','Price: Low to High':'p.price ASC','Price: High to Low':'p.price DESC','Popularity':'p.rating_count DESC','Recommended':'p.is_new DESC,p.rating DESC'}.get(sort,'p.is_new DESC')
    sql+=' ORDER BY '+order
    items=query(sql,params)
    for p in items:
        variants=query('SELECT * FROM product_variants WHERE product_id=?',(p['id'],))
        p['variants']=variants
        if sizes: p['variants']=[v for v in variants if v['size'] in sizes]
        if colours: p['variants']=[v for v in p['variants'] if v['colour'] in colours]
        p['available_stock']=sum(v['stock'] for v in p['variants'])
    return [p for p in items if p['variants']]

def get_product(product_id):
    p=query('SELECT p.*,c.name category FROM products p LEFT JOIN categories c ON c.id=p.category_id WHERE p.id=? AND p.is_active=1',(product_id,),one=True)
    if p:
        p['variants']=query('SELECT * FROM product_variants WHERE product_id=?',(product_id,))
        p['images']=query('SELECT image_url FROM product_images WHERE product_id=? ORDER BY sort_order',(product_id,))
    return p

def categories(): return query('SELECT * FROM categories ORDER BY name')

def create_product(data, variants):
    with get_db() as db:
        cur=db.execute("INSERT INTO products(sku,name,brand,description,category_id,price,mrp,rating,image_url,is_new) VALUES(?,?,?,?,?,?,?,?,?,?)",(data['sku'],data['name'],data['brand'],data['description'],data['category_id'],data['price'],data['mrp'],data['rating'],data['image_url'],data['is_new']))
        pid=cur.lastrowid
        for v in variants: db.execute('INSERT INTO product_variants(product_id,size,colour,stock) VALUES(?,?,?,?)',(pid,v['size'],v['colour'],v['stock']))
    return pid

def update_stock(variant_id, change, reason):
    with get_db() as db:
        row=db.execute('SELECT stock FROM product_variants WHERE id=?',(variant_id,)).fetchone()
        if not row or row['stock']+change<0: raise ValueError('Insufficient stock.')
        db.execute('UPDATE product_variants SET stock=stock+? WHERE id=?',(change,variant_id))
        db.execute('INSERT INTO inventory_movements(variant_id,change_qty,reason) VALUES(?,?,?)',(variant_id,change,reason))
