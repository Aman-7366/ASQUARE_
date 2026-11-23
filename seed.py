"""Idempotent sample catalogue seed."""
from database import get_db,query
from auth import ensure_admin
from config import ADMIN_EMAIL,ADMIN_PASSWORD

SUBCATEGORIES={
'Men':['T-shirts','Shirts','Jeans','Trousers','Jackets','Hoodies','Ethnic wear','Sportswear'],
'Women':['Dresses','Tops','Kurtis','Sarees','Jeans','Trousers','Co-ord sets','Ethnic wear'],
'Kids':["Boys' clothing","Girls' clothing",'Baby clothing','Party wear'],
'Footwear':['Sneakers','Casual shoes','Formal shoes','Sandals'],
'Accessories':['Handbags','Watches','Sunglasses','Belts','Wallets']
}

PRODUCTS=[
('ASQ-M001','Essential Cotton Tee','A SQUARE','Premium 240 GSM cotton, relaxed fit.',"T-shirts",799,1299,'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=900',1,[('S','Black',12),('M','Black',20),('L','Black',14),('M','White',10)]),
('ASQ-M002','Oxford Everyday Shirt','A SQUARE','A crisp everyday Oxford shirt.',"Shirts",1499,2299,'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=900',1,[('M','Blue',8),('L','Blue',10),('XL','Blue',6)]),
('ASQ-W001','Linen Blend Co-ord','A SQUARE','Easy tailoring in a breathable linen blend.',"Co-ord sets",2199,3299,'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=900',1,[('S','Beige',8),('M','Beige',10),('L','Beige',7)]),
('ASQ-W002','Minimal Day Dress','A SQUARE','A fluid silhouette for everyday moments.',"Dresses",1899,2799,'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=900',0,[('S','Black',6),('M','Black',8),('L','Black',5)]),
('ASQ-K001','Kids Weekend Set','A SQUARE Kids','Soft cotton set made for play.',"Boys' clothing",999,1499,'https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=900',1,[('4-5Y','Blue',7),('6-7Y','Blue',8)]),
('ASQ-F001','Everyday Court Sneakers','A SQUARE','Clean low-top sneakers with cushioned comfort.',"Sneakers",2499,3499,'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=900',1,[('7','White',5),('8','White',7),('9','White',8),('10','White',4)]),
('ASQ-A001','Structured Daily Tote','A SQUARE','A versatile structured tote for every day.',"Handbags",1799,2499,'https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=900',0,[('One Size','Tan',9)]),
('ASQ-M003','Relaxed Denim','A SQUARE','Modern straight fit denim with a soft hand feel.',"Jeans",1999,2999,'https://images.unsplash.com/photo-1542272604-787c3835535d?w=900',0,[('30','Blue',8),('32','Blue',10),('34','Blue',6)])]

def seed():
    ensure_admin(ADMIN_EMAIL,ADMIN_PASSWORD)
    with get_db() as db:
        for name in ['Men','Women','Kids','Footwear','Accessories']:
            db.execute('INSERT OR IGNORE INTO categories(name,slug) VALUES(?,?)',(name,name.lower()))
        for parent, children in SUBCATEGORIES.items():
            parent_id=db.execute('SELECT id FROM categories WHERE name=?',(parent,)).fetchone()['id']
            for child in children:
                db.execute('INSERT OR IGNORE INTO categories(name,parent_id,slug) VALUES(?,?,?)',(child,parent_id,child.lower().replace(' ','-').replace("'",'')))
        for sku,name,brand,desc,cat,price,mrp,img,new,variants in PRODUCTS:
            exists=db.execute('SELECT id FROM products WHERE sku=?',(sku,)).fetchone()
            if exists: continue
            cid=db.execute('SELECT id FROM categories WHERE name=?',(cat,)).fetchone()['id']
            cur=db.execute('INSERT INTO products(sku,name,brand,description,category_id,price,mrp,image_url,is_new) VALUES(?,?,?,?,?,?,?,?,?)',(sku,name,brand,desc,cid,price,mrp,img,new))
            for size,colour,stock in variants: db.execute('INSERT INTO product_variants(product_id,size,colour,stock) VALUES(?,?,?,?)',(cur.lastrowid,size,colour,stock))
        db.execute("INSERT OR IGNORE INTO coupons(code,discount_percent,min_order,max_discount) VALUES('WELCOME10',10,999,500)")
