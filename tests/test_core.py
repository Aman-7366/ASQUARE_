import os
import tempfile
import unittest

TEST_DB = os.path.join(tempfile.gettempdir(), 'asquare_test_suite.db')
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
os.environ['DB_PATH'] = TEST_DB

from database import init_db, get_db, query
from auth import hash_password, verify_password, register, login
from checkout import totals
from payments import verify_checkout_signature, verify_webhook_signature
from seed import seed
from products import list_products
import hashlib, hmac

class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed()

    def test_password_hash(self):
        encoded = hash_password('AsecurePassword123!')
        self.assertTrue(verify_password('AsecurePassword123!', encoded))
        self.assertFalse(verify_password('wrong', encoded))

    def test_register_login(self):
        email = 'test_user_asq@example.com'
        with get_db() as db:
            db.execute('DELETE FROM users WHERE email=?', (email,))
        register('Test User', email, 'AsecurePassword123!')
        self.assertEqual(login(email, 'AsecurePassword123!')['email'], email)
        self.assertIsNone(login(email, 'wrong-password'))

    def test_totals(self):
        items = [{'price': 1000, 'quantity': 2}]
        subtotal, discount, delivery, total = totals(items)
        self.assertEqual((subtotal, discount, delivery, total), (2000, 0, 0, 2000))

    def test_seeded_catalogue_and_category_tree(self):
        self.assertGreaterEqual(len(list_products()), 8)
        self.assertGreaterEqual(len(query('SELECT id FROM categories')), 30)
        self.assertTrue(list_products(category='Men'))
        self.assertTrue(list_products(category='T-shirts'))

    def test_checkout_signature(self):
        secret = 'test_secret'
        order_id, payment_id = 'order_test', 'pay_test'
        signature = hmac.new(secret.encode(), f'{order_id}|{payment_id}'.encode(), hashlib.sha256).hexdigest()
        import payments
        old = payments.RAZORPAY_KEY_SECRET
        payments.RAZORPAY_KEY_SECRET = secret
        try:
            self.assertTrue(verify_checkout_signature(order_id, payment_id, signature))
            self.assertFalse(verify_checkout_signature(order_id, payment_id, 'bad'))
        finally:
            payments.RAZORPAY_KEY_SECRET = old

if __name__ == '__main__':
    unittest.main(verbosity=2)
