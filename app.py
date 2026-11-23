import streamlit as st
from config import APP_NAME,TAGLINE,CURRENCY,DELIVERY_FEE,FREE_DELIVERY_OVER,RAZORPAY_KEY_ID
from database import init_db,query,get_db
from seed import seed
from auth import login,register
from products import list_products,get_product,categories,create_product
from cart import add_to_cart,cart_items,set_quantity,remove_item,toggle_wishlist,wishlist
from checkout import create_order,confirm_razorpay,user_orders,order_items,totals
from admin import metrics,all_orders,set_order_status,set_product_active,create_coupon
from admin_tools import file_to_data_uri,product_images,add_images,remove_images,update_product,variants_for,update_variant,add_variant
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title=f'{APP_NAME} | {TAGLINE}',page_icon='◼',layout='wide',initial_sidebar_state='expanded')
init_db(); seed()
st.markdown('<style>'+open('style.css',encoding='utf-8').read()+'</style>',unsafe_allow_html=True)
st.markdown('<div class="asq-announcement">THE NEW SEASON IS HERE · EXTRA 10% OFF WITH WELCOME10</div>',unsafe_allow_html=True)
if 'user' not in st.session_state: st.session_state.user=None
if 'page' not in st.session_state: st.session_state.page='Home'
if 'search' not in st.session_state: st.session_state.search=''
user=st.session_state.user

def uget(key,default=''):
    try: return user[key] or default
    except Exception: return default

def navigate_to(page):
    """Change the active view and request a clean rerun at the top of the page."""
    st.session_state.page = page
    st.session_state['_scroll_to_top'] = True
    st.rerun()

# ---------- Header: clickable logo (centre) + account circle (top right) ----------
logo_svg=open('assets/asquare-logo.svg',encoding='utf-8').read()
h1,h2,h3=st.columns([1,3,1])
with h2:
    with st.container(key='logo_home'):
        st.markdown(f'<div class="asq-logo">{logo_svg}</div>',unsafe_allow_html=True)
        if st.button('Home',key='logo_btn'):
            navigate_to('Home')
with h3:
    with st.container(key='acct_in' if user else 'acct_out'):
        label=str(uget('name','U'))[:1].upper() if user else '👤'
        with st.popover(label):
            if user:
                st.markdown(f"**{uget('name')}**")
                if uget('email'): st.caption(uget('email'))
                if st.button('My account',key='pop_account',use_container_width=True): navigate_to('Account')
                if st.button('My orders',key='pop_orders',use_container_width=True): navigate_to('My Orders')
                if st.button('Wishlist',key='pop_wishlist',use_container_width=True): navigate_to('Wishlist')
                if uget('role')=='admin' and st.button('Admin dashboard',key='pop_admin',use_container_width=True): navigate_to('Admin')
                if st.button('Log out',key='pop_logout',use_container_width=True): st.session_state.user=None; navigate_to('Home')
            else:
                st.markdown('**Welcome to A SQUARE**')
                st.caption('Sign in to track orders and save favourites.')
                if st.button('Login / Register',key='pop_login',use_container_width=True): navigate_to('Account')

with st.sidebar:
    st.markdown('## A SQUARE')
    st.caption('FASHION. STYLE. CONFIDENCE.')
    for page in ['Home','All Category','Men','Women','Kids','Footwear','Accessories','Wishlist','My Bag','My Orders','Account']:
        if st.button(page,use_container_width=True,key='nav_'+page): navigate_to(page)
    st.divider()
    if user:
        st.write(f"Hello, **{user['name']}**")
        if user['role']=='admin' and st.button('Admin dashboard',use_container_width=True): navigate_to('Admin')
        if st.button('Log out',use_container_width=True): st.session_state.user=None; navigate_to('Home')
    else:
        if st.button('Login / Register',use_container_width=True): navigate_to('Account')
    st.caption('India · Prices in INR')

bag_count=len(cart_items(user['id'])) if user else 0
c1,c2,c3=st.columns([4,1,1])
with c1: st.session_state.search=st.text_input('Search styles, brands and more',value=st.session_state.search,placeholder='Search the collection…',label_visibility='collapsed')
with c2:
    if st.button('♡ Wishlist',use_container_width=True): navigate_to('Wishlist')
with c3:
    if st.button(f'Bag ({bag_count})',use_container_width=True): navigate_to('My Bag')

# ---------- Top navigation bar (always visible, no sidebar needed) ----------
NAV=['Home','All Category','Men','Women','Kids','Footwear','Accessories','My Orders']
if user and user['role']=='admin': NAV.append('Admin')
nav_cols=st.columns(len(NAV))
for col,pg in zip(nav_cols,NAV):
    if col.button(pg.upper(),key='top_'+pg,use_container_width=True):
        navigate_to(pg)
st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)


def section(title,subtitle=''):
    st.markdown(f'<div class="asq-section">{title}</div><div class="asq-sub">{subtitle}</div>',unsafe_allow_html=True)

def product_grid(items,cols=4,prefix=''):
    if not items: st.info('No products match these filters.'); return
    for start in range(0,len(items),cols):
        row=st.columns(cols)
        for col,p in zip(row,items[start:start+cols]):
            with col:
                off=max(0,round((p['mrp']-p['price'])*100/p['mrp'])) if p['mrp'] else 0
                st.markdown(f'''<div class="asq-card"><img src="{p['image_url']}"/><h4>{p['name']}</h4><div style="color:#777;font-size:11px">{p['brand']}</div><div class="asq-price">₹{p['price']:,}<span class="asq-mrp">₹{p['mrp']:,}</span><span class="asq-off">{off}% OFF</span></div><div style="font-size:11px;color:#927b4c">★ {p['rating']:.1f} · {p['rating_count']} ratings</div></div>''',unsafe_allow_html=True)
                sizes=sorted(set(v['size'] for v in p.get('variants',[]) if v['stock']>0))
                if sizes:
                    size=st.selectbox('Size',sizes,key=f"{prefix}size_{p['id']}",label_visibility='collapsed')
                    colour_options=[v['colour'] for v in p['variants'] if v['size']==size and v['stock']>0]
                    colour=st.selectbox('Colour',colour_options,key=f"{prefix}colour_{p['id']}",label_visibility='collapsed')
                else: size=colour=None
                a,b=st.columns(2)
                with a:
                    if st.button('View',key=f"{prefix}view_{p['id']}",use_container_width=True): st.session_state.selected_product=p['id']; navigate_to('Product')
                with b:
                    if st.button('♡',key=f"{prefix}wish_{p['id']}",use_container_width=True):
                        if not user: st.warning('Please log in to save favourites.')
                        else: toggle_wishlist(user['id'],p['id']); st.toast('Wishlist updated')
                if st.button('ADD TO BAG',key=f"{prefix}add_{p['id']}",use_container_width=True):
                    if not user: st.warning('Please log in before adding to bag.')
                    elif not size or not colour: st.warning('Choose a size and colour.')
                    else:
                        variant=next(v for v in p['variants'] if v['size']==size and v['colour']==colour)
                        try: add_to_cart(user['id'],variant['id']); st.success('Added to your bag.')
                        except ValueError as e: st.error(str(e))

def product_page(pid):
    p=get_product(pid)
    if not p: st.error('Product not found.'); return
    left,right=st.columns([1.1,1])
    with left:
        st.image(p['image_url'],use_container_width=True)
        for im in p['images']: st.image(im['image_url'],width=120)
    with right:
        st.caption(p['brand'].upper()); st.title(p['name']); st.write(p['description'])
        st.markdown(f"### ₹{p['price']:,}  ~~₹{p['mrp']:,}~~")
        st.caption(f"Inclusive of all taxes · {p['rating']} ★ ({p['rating_count']} ratings)")
        available=[v for v in p['variants'] if v['stock']>0]
        if not available: st.error('Currently out of stock.'); return
        size=st.selectbox('Select size',sorted(set(v['size'] for v in available)))
        colour=st.selectbox('Select colour',sorted(set(v['colour'] for v in available if v['size']==size)))
        variant=next(v for v in available if v['size']==size and v['colour']==colour)
        st.caption(f"{variant['stock']} available")
        qty=st.number_input('Quantity',1,min(variant['stock'],10),1)
        pin=st.text_input('Delivery PIN code',max_chars=6,placeholder='Enter 6-digit PIN code')
        if st.button('CHECK DELIVERY'):
            if pin.isdigit() and len(pin)==6: st.success('PIN format looks valid. Final serviceability is confirmed at dispatch.')
            else: st.error('Enter a valid 6-digit Indian PIN code.')
        if st.button('ADD TO BAG',use_container_width=True):
            if not user: st.warning('Please log in first.')
            else:
                try: add_to_cart(user['id'],variant['id'],int(qty)); st.success('Added to your bag.')
                except ValueError as e: st.error(str(e))
        if st.button('♡ SAVE TO WISHLIST',use_container_width=True):
            if user: toggle_wishlist(user['id'],pid); st.toast('Wishlist updated')
            else: st.warning('Please log in first.')
        st.divider(); st.subheader('Product details'); st.write(p['description']); st.write('Premium finish · Easy care · Designed for everyday confidence.')
        st.subheader('Size guide'); st.write('Please refer to the size selector. If between sizes, choose the larger size for a relaxed fit.')
        st.subheader('Customer reviews'); reviews=query('SELECT r.*,u.name FROM reviews r JOIN users u ON u.id=r.user_id WHERE product_id=? ORDER BY created_at DESC',(pid,))
        if reviews:
            for r in reviews: st.write(f"{'★'*r['rating']} — **{r['name']}**: {r['body']}")
        else: st.caption('Be the first to review this piece.')

def thumb(u):
    return f'<img src="{u}" style="width:100%;max-width:110px;height:110px;object-fit:cover;border:1px solid #e5dfd5"/>'

def edit_product_panel(pid):
    p=get_product(pid)
    if not p: st.error('Product not found.'); return
    cats=categories(); names=[c['name'] for c in cats]
    cur=next((c['name'] for c in cats if c['id']==p.get('category_id')),names[0])
    gallery=product_images(pid); vrows=variants_for(pid)
    with st.container(border=True):
        st.markdown(f"#### Edit product · {p['name']}")
        with st.form(f'edit_form_{pid}'):
            name=st.text_input('Product name',value=p['name'])
            brand=st.text_input('Brand',value=p.get('brand') or '')
            desc=st.text_area('Description',value=p.get('description') or '')
            catname=st.selectbox('Category',names,index=names.index(cur))
            a,b=st.columns(2)
            price=a.number_input('Selling price',min_value=1,value=int(p['price']))
            mrp=b.number_input('MRP',min_value=1,value=int(p['mrp']))
            st.markdown('**Current pictures**')
            tiles=st.columns(5)
            tiles[0].markdown(thumb(p['image_url']),unsafe_allow_html=True); tiles[0].caption('Main picture')
            remove=[]
            for n,g in enumerate(gallery):
                col=tiles[(n+1)%5]
                col.markdown(thumb(g['image_url']),unsafe_allow_html=True)
                if col.checkbox('Remove',key=f"rm_{pid}_{g['id']}"): remove.append(g['id'])
            newpics=st.file_uploader('Add pictures (choose one or many)',type=['png','jpg','jpeg','webp'],accept_multiple_files=True,key=f'up_{pid}')
            as_main=st.checkbox('Make the first new picture the main picture',key=f'asmain_{pid}')
            st.markdown('**Sizes, colours and stock** (edit any cell)')
            df=pd.DataFrame(vrows,columns=['id','size','colour','stock'])
            edited=st.data_editor(df,hide_index=True,disabled=['id'],use_container_width=True,key=f've_{pid}')
            n1,n2,n3=st.columns(3)
            ns=n1.text_input('Add new size',key=f'ns_{pid}'); nc=n2.text_input('Colour for new size',value='Black',key=f'nc_{pid}'); nst=n3.number_input('Stock for new size',min_value=0,value=10,key=f'nst_{pid}')
            save=st.form_submit_button('SAVE CHANGES')
        if save:
            try:
                if not name.strip(): raise ValueError('Product name is required.')
                if price>mrp: raise ValueError('Selling price cannot be higher than MRP.')
                main=p['image_url']; extras=[]
                new=[file_to_data_uri(f) for f in newpics]
                if new:
                    if as_main: extras=[p['image_url']]+new[1:]; main=new[0]
                    else: extras=new
                update_product(pid,name=name.strip(),brand=brand.strip(),description=desc,category_id=next(c['id'] for c in cats if c['name']==catname),price=int(price),mrp=int(mrp),image_url=main)
                if remove: remove_images(remove)
                if extras: add_images(pid,extras)
                for _,r in edited.iterrows(): update_variant(int(r['id']),str(r['size']).strip(),str(r['colour']).strip(),int(r['stock']))
                if ns.strip(): add_variant(pid,ns.strip(),nc.strip() or 'Black',int(nst))
                st.session_state.edit_pid=None; st.session_state.flash='Product updated.'; st.rerun()
            except Exception as e: st.error(f'Could not save: {e}')
        if st.button('Close editor',key=f'close_{pid}'): st.session_state.edit_pid=None; st.rerun()

page=st.session_state.page
if st.session_state.pop('_scroll_to_top', False):
    components.html("""<script>
    try {
      window.parent.scrollTo({top: 0, left: 0, behavior: 'instant'});
      const app = window.parent.document.querySelector('[data-testid=\"stAppViewContainer\"]');
      if (app) app.scrollTo({top: 0, left: 0, behavior: 'instant'});
      const main = window.parent.document.querySelector('section.main');
      if (main) main.scrollTo({top: 0, left: 0, behavior: 'instant'});
    } catch (e) {}
    </script>""", height=0, width=0)
if page=='Home':
    st.markdown('<div class="asq-hero"><div><div class="asq-kicker">A SQUARE · NEW SEASON 2026</div><h1>Style that speaks<br/>without saying a word.</h1><p>Thoughtful essentials. Confident everyday dressing.</p></div></div>',unsafe_allow_html=True)
    x,y,z=st.columns(3)
    for col,(name,desc) in zip([x,y,z],[('MEN','Modern essentials'),('WOMEN','Effortless statements'),('KIDS','Made for little moments')]):
        with col:
            st.markdown(f'<div style="background:#e9e2d6;padding:28px;text-align:center"><div style="font:26px Playfair Display">{name}</div><div style="font-size:11px;letter-spacing:2px">{desc}</div></div>',unsafe_allow_html=True)
            if st.button(f'EXPLORE {name}',key='explore'+name,use_container_width=True): navigate_to(name.title())
    section('Trending now','The pieces everyone is reaching for.')
    product_grid(list_products(sort='Popularity')[:4],prefix='trend_')
    section('New arrivals','Fresh additions to your wardrobe.')
    product_grid([p for p in list_products() if p['is_new']][:4],prefix='new_')
    section('The A SQUARE edit','Build a wardrobe that feels unmistakably yours.')
    st.markdown('<div class="asq-footer">A SQUARE · FASHION. STYLE. CONFIDENCE.<br/><br/>Customer care · support@asquare.com · +91 7366011867<br/>Instagram · Facebook · Pinterest<br/><br/>© 2026 A SQUARE. All rights reserved.</div>',unsafe_allow_html=True)
elif page in ['All Category','Men','Women','Kids','Footwear','Accessories']:
    section(page,'Discover considered pieces for every day.')
    f1,f2,f3,f4=st.columns(4)
    with f1: cat=st.selectbox('Category',['All']+[c['name'] for c in categories()],index=(['All']+[c['name'] for c in categories()]).index(page) if page in [c['name'] for c in categories()] else 0)
    with f2: max_price=st.slider('Maximum price (₹)',500,10000,10000,500)
    with f3: rating=st.selectbox('Customer rating',['Any',3.0,4.0,4.5])
    with f4: sort=st.selectbox('Sort by',['Recommended','Newest arrivals','Price: Low to High','Price: High to Low','Popularity'])
    product_grid(list_products(st.session_state.search,cat,0,max_price,min_rating=0 if rating=='Any' else rating,sort=sort))
elif page=='Product': product_page(st.session_state.get('selected_product'))
elif page=='Account' and user:
    section('My account','Your details and quick links.')
    st.markdown(f"**Name:** {uget('name')}")
    if uget('email'): st.markdown(f"**Email:** {uget('email')}")
    if uget('phone'): st.markdown(f"**Mobile:** {uget('phone')}")
    st.markdown(f"**Account type:** {str(uget('role','customer')).title()}")
    st.write('')
    a,b,c,d=st.columns(4)
    if a.button('MY ORDERS',key='acc_orders',use_container_width=True): navigate_to('My Orders')
    if b.button('WISHLIST',key='acc_wish',use_container_width=True): navigate_to('Wishlist')
    if c.button('MY BAG',key='acc_bag',use_container_width=True): navigate_to('My Bag')
    if d.button('LOG OUT',key='acc_logout',use_container_width=True): st.session_state.user=None; navigate_to('Home')
elif page=='Account':
    section('Your A SQUARE account','Sign in for a more personal shopping experience.')
    tab1,tab2=st.tabs(['Login','Create account'])
    with tab1:
        with st.form('login'):
            email=st.text_input('Email'); password=st.text_input('Password',type='password'); submit=st.form_submit_button('SIGN IN')
        if submit:
            found=login(email,password)
            if found: st.session_state.user=found; st.success('Welcome back.'); st.rerun()
            else: st.error('Email or password is incorrect.')
    with tab2:
        with st.form('register'):
            name=st.text_input('Full name'); em=st.text_input('Email address'); phone=st.text_input('Mobile number'); pw=st.text_input('Password (10+ characters)',type='password'); submit2=st.form_submit_button('CREATE ACCOUNT')
        if submit2:
            try: st.session_state.user=register(name,em,pw,phone); st.success('Account created.'); st.rerun()
            except Exception as e: st.error(str(e))
elif page=='Wishlist':
    section('Your wishlist')
    if not user: st.info('Log in to see your wishlist.')
    else: product_grid(wishlist(user['id']))
elif page=='My Bag':
    section('Shopping bag','Your selected pieces, ready when you are.')
    if not user: st.info('Please log in to view your bag.')
    else:
        items=cart_items(user['id'])
        if not items: st.info('Your bag is waiting for something special.')
        for i in items:
            a,b,c=st.columns([4,1,1]); a.write(f"**{i['name']}** · {i['size']} / {i['colour']} · ₹{i['price']:,}")
            qty=b.number_input('Qty',1,i['stock'],i['quantity'],key=f"qty_{i['cart_item_id']}")
            if qty!=i['quantity']: set_quantity(user['id'],i['cart_item_id'],qty); st.rerun()
            if c.button('Remove',key=f"remove_{i['cart_item_id']}"): remove_item(user['id'],i['cart_item_id']); st.rerun()
        if items:
            coupon=st.text_input('Coupon code',placeholder='WELCOME10')
            subtotal,discount,delivery,total=totals(items,coupon)
            st.write(f'Subtotal: ₹{subtotal:,}'); st.write(f'Discount: −₹{discount:,}'); st.write(f'Delivery: ₹{delivery:,}'); st.markdown(f'## Total: ₹{total:,}')
            if st.button('PROCEED TO CHECKOUT',use_container_width=True): st.session_state.coupon=coupon; navigate_to('Checkout')
elif page=='Checkout':
    section('Checkout','A few details and your order is on its way.')
    if not user: st.info('Please log in first.')
    elif not cart_items(user['id']): st.info('Your bag is empty.')
    else:
        with st.form('checkout'):
            st.subheader('Shipping address'); name=st.text_input('Recipient name',value=user['name']); phone=st.text_input('Mobile number'); line1=st.text_input('Address line 1'); line2=st.text_input('Address line 2'); city=st.text_input('City'); state=st.text_input('State'); pin=st.text_input('PIN code',max_chars=6)
            method=st.radio('Payment method',['Cash on Delivery','Razorpay (UPI / Cards / Netbanking)'])
            coupon=st.text_input('Coupon',value=st.session_state.get('coupon',''))
            place=st.form_submit_button('PLACE ORDER')
        if place:
            if not all([name,phone,line1,city,state]) or not pin.isdigit() or len(pin)!=6: st.error('Complete all required address fields and enter a valid PIN code.')
            elif method.startswith('Razorpay') and not RAZORPAY_KEY_ID: st.error('Razorpay is not configured. Use COD or add test keys to .env.')
            else:
                try:
                    order=create_order(user['id'],{'name':name,'phone':phone,'line1':line1,'line2':line2,'city':city,'state':state,'pincode':pin},'Razorpay' if method.startswith('Razorpay') else 'COD',coupon or None)
                    st.session_state.last_order=order; navigate_to('Order confirmation')
                except Exception as e: st.error(f'Could not place order: {e}')
elif page=='Order confirmation':
    order=st.session_state.get('last_order')
    if order:
        section('Thank you for shopping A SQUARE','Your order has been created.')
        st.success(f"Order {order['order_number']} · ₹{order['total']:,}")
        if order.get('razorpay_order'):
            rp=order['razorpay_order']; st.warning('Razorpay order created. Complete payment using the secure Razorpay checkout integration before treating this order as paid.')
            st.code(f"Razorpay Order ID: {rp['id']}\nKey ID: {RAZORPAY_KEY_ID}")
            st.caption('This starter project creates and verifies Razorpay orders server-side. Add the official Razorpay Checkout JS in a trusted custom component for a production payment UI.')
        else: st.info('Payment method: Cash on Delivery. Payment status: COD.')
        if st.button('CONTINUE SHOPPING'): navigate_to('All Category')
elif page=='My Orders':
    section('Your orders','Every order, all in one place.')
    if not user: st.info('Log in to view orders.')
    else:
        for o in user_orders(user['id']):
            with st.expander(f"{o['order_number']} · ₹{o['total']:,} · {o['status']}"):
                st.write(f"Placed: {o['created_at']} · Payment: {o['payment_status']}")
                for i in order_items(o['id']): st.write(f"{i['product_name']} — {i['size']} / {i['colour']} × {i['quantity']}")
                if o['status'] in ['Order Placed','Payment Confirmed','Processing'] and st.button('REQUEST CANCELLATION',key=f"cancel_{o['id']}"):
                    st.warning('Cancellation request noted. Contact support to complete the request.')
elif page=='Admin':
    if not user or user['role']!='admin': st.error('Admin access required.')
    else:
        section('Admin dashboard','A clear view of your store.')
        m=metrics(); cols=st.columns(4)
        for c,(label,val) in zip(cols,[('Sales',f"₹{m['sales']:,}"),('Orders',m['orders']),('Customers',m['customers']),('Products',m['products'])]): c.metric(label,val)
        t1,t2,t3=st.tabs(['Orders','Products','Coupons'])
        STATUSES=['Order Placed','Payment Confirmed','Processing','Packed','Shipped','Out for Delivery','Delivered','Cancelled']
        with t1:
            for o in all_orders():
                c1,c2,c3=st.columns([3,2,2]); c1.write(f"**{o['order_number']}** · {o['customer']} · ₹{o['total']:,}"); c2.write(o['payment_status'])
                new_status=c3.selectbox('Status',STATUSES,index=STATUSES.index(o['status']) if o['status'] in STATUSES else 0,key=f"status_{o['id']}")
                if c3.button('Update',key=f"update_{o['id']}"): set_order_status(o['id'],new_status); st.rerun()
        with t2:
            if st.session_state.get('flash'): st.success(st.session_state.pop('flash'))
            st.subheader('Add product')
            with st.form('new_product'):
                sku=st.text_input('SKU'); pname=st.text_input('Product name'); brand=st.text_input('Brand',value='A SQUARE'); desc=st.text_area('Description'); catname=st.selectbox('Category',[c['name'] for c in categories()]); price=st.number_input('Selling price',min_value=1,value=999); mrp=st.number_input('MRP',min_value=1,value=1499)
                pics=st.file_uploader('Product pictures (choose one or many; the first is the main picture)',type=['png','jpg','jpeg','webp'],accept_multiple_files=True)
                image=st.text_input('Or paste a main image URL (optional)')
                sizes=st.text_input('Sizes (comma separated)',value='S,M,L'); colour=st.text_input('Colour',value='Black'); stock=st.number_input('Stock per size',min_value=0,value=10); add=st.form_submit_button('CREATE PRODUCT')
            if add:
                try:
                    if not pics and not image.strip(): raise ValueError('Add at least one picture or an image URL.')
                    uris=[file_to_data_uri(f) for f in pics]
                    main=uris[0] if uris else image.strip(); extras=uris[1:]
                    cid=next(c['id'] for c in categories() if c['name']==catname)
                    create_product({'sku':sku,'name':pname,'brand':brand,'description':desc,'category_id':cid,'price':int(price),'mrp':int(mrp),'rating':4.5,'image_url':main,'is_new':1},[{'size':s.strip(),'colour':colour,'stock':int(stock)} for s in sizes.split(',') if s.strip()])
                    if extras:
                        found=query('SELECT id FROM products WHERE sku=?',(sku,))
                        if found: add_images(found[0]['id'],extras)
                    st.session_state.flash='Product created.'; st.rerun()
                except Exception as e: st.error(str(e))
            st.subheader('All products')
            for p in query('SELECT id,name,is_active FROM products ORDER BY id DESC'):
                c1,c2,c3=st.columns([4,1,1]); c1.write(p['name'])
                if c2.button('Edit',key=f"edit_{p['id']}",use_container_width=True): st.session_state.edit_pid=p['id']; st.rerun()
                if c3.button('Deactivate' if p['is_active'] else 'Activate',key=f"active_{p['id']}",use_container_width=True): set_product_active(p['id'],not p['is_active']); st.rerun()
                if st.session_state.get('edit_pid')==p['id']: edit_product_panel(p['id'])
        with t3:
            with st.form('coupon_form'):
                code=st.text_input('Code'); percent=st.number_input('Discount %',1,80,10); minimum=st.number_input('Minimum order ₹',0,100000,999); cap=st.number_input('Maximum discount ₹',1,10000,500); save=st.form_submit_button('CREATE COUPON')
            if save:
                try: create_coupon(code,percent,minimum,cap); st.success('Coupon created.')
                except Exception as e: st.error(str(e))

st.markdown('<div class="asq-footer">A SQUARE · FASHION. STYLE. CONFIDENCE. · MADE FOR INDIA</div>',unsafe_allow_html=True)