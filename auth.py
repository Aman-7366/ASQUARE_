"""Authentication helpers. Passwords are stored using PBKDF2-HMAC-SHA256."""
import hashlib, hmac, secrets
from database import get_db, query

ITERATIONS=310_000

def hash_password(password: str) -> str:
    if len(password)<10: raise ValueError('Password must contain at least 10 characters.')
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt, expected=encoded.split('$')
        if scheme!='pbkdf2_sha256': return False
        actual=hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError): return False

def register(name,email,password,phone=''):
    email=email.strip().lower()
    if not name.strip() or '@' not in email: raise ValueError('Enter a valid name and email address.')
    with get_db() as db:
        cur=db.execute('INSERT INTO users(name,email,password_hash,phone) VALUES(?,?,?,?)',
                       (name.strip(),email,hash_password(password),phone.strip()))
        user_id=cur.lastrowid
        db.execute('INSERT INTO carts(user_id) VALUES(?)',(user_id,))
    return query('SELECT id,name,email,role FROM users WHERE id=?',(user_id,),one=True)

def login(email,password):
    user=query('SELECT * FROM users WHERE email=? AND is_active=1',(email.strip().lower(),),one=True)
    if not user or not verify_password(password,user['password_hash']): return None
    return {k:user[k] for k in ('id','name','email','role')}

def ensure_admin(email,password):
    if not email or not password: return
    existing=query('SELECT id FROM users WHERE email=?',(email.lower(),),one=True)
    if existing:
        with get_db() as db: db.execute("UPDATE users SET role='admin' WHERE id=?",(existing['id'],))
    else:
        with get_db() as db:
            cur=db.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')",
                           ('A SQUARE Admin',email.lower(),hash_password(password)))
            db.execute('INSERT INTO carts(user_id) VALUES(?)',(cur.lastrowid,))
