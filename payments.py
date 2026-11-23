"""Razorpay REST integration. Secrets are read only on the server."""
import hashlib,hmac,json
import requests
from config import RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET,RAZORPAY_WEBHOOK_SECRET,RAZORPAY_BASE_URL

def create_razorpay_order(amount_paise,receipt):
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET: raise RuntimeError('Razorpay keys are not configured.')
    response=requests.post(RAZORPAY_BASE_URL+'/orders',auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET),
        json={'amount':int(amount_paise),'currency':'INR','receipt':receipt,'payment_capture':1},timeout=20)
    response.raise_for_status(); return response.json()

def verify_checkout_signature(order_id,payment_id,signature):
    if not RAZORPAY_KEY_SECRET: return False
    msg=f'{order_id}|{payment_id}'.encode()
    expected=hmac.new(RAZORPAY_KEY_SECRET.encode(),msg,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature or '')

def verify_webhook_signature(raw_body,signature):
    if not RAZORPAY_WEBHOOK_SECRET: return False
    expected=hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(),raw_body,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature or '')

def fetch_payment(payment_id):
    response=requests.get(RAZORPAY_BASE_URL+f'/payments/{payment_id}',auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET),timeout=20)
    response.raise_for_status(); return response.json()
