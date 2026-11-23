"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv
load_dotenv()

APP_NAME = "A SQUARE"
TAGLINE = "Fashion. Style. Confidence."
DB_PATH = os.getenv("DB_PATH", "data/a_square.db")
CURRENCY = "₹"
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_BASE_URL = "https://api.razorpay.com/v1"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@asquare.local").lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SESSION_COOKIE_TTL = int(os.getenv("SESSION_COOKIE_TTL", "86400"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
DELIVERY_FEE = int(os.getenv("DELIVERY_FEE", "79"))
FREE_DELIVERY_OVER = int(os.getenv("FREE_DELIVERY_OVER", "1999"))
