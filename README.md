# A SQUARE — Premium Fashion Storefront

A modular Python/Streamlit commerce application for the A SQUARE fashion brand. It includes a premium storefront theme, seeded catalogue and category tree, customer registration/login, catalogue search and filters, wishlist, cart, coupons, COD checkout, order records, admin order/product/coupon controls, SQLite persistence, and server-side Razorpay order/signature/webhook helpers.

> **Scope and launch safety:** This is a runnable local commerce MVP, not yet a production-ready marketplace. Razorpay order creation, checkout-signature verification, payment fetching, and webhook-signature verification are implemented server-side. The Streamlit UI does not yet embed the official Razorpay Checkout modal or expose a complete trusted payment-callback bridge; therefore do not accept real online payments until that bridge is implemented and end-to-end tested. COD works in the local demo. PIN validation checks format only, not courier serviceability. Cancellation/return/refund workflows, password-reset delivery, saved-address management, real email/SMS notifications, image upload/object storage, and courier tracking integrations still need provider-backed implementation. The admin currently supports product creation/activation, order status updates and coupon creation; it is not a full ERP console.

## Project structure

```text
a_square/
├── app.py                 # Streamlit storefront, customer flows and admin UI
├── admin.py               # Admin queries and actions
├── auth.py                # PBKDF2 password hashing and authentication
├── cart.py                # Cart and wishlist operations
├── checkout.py            # Totals, order creation and payment confirmation
├── config.py              # dotenv/environment configuration
├── database.py            # SQLite schema and transaction helpers
├── init_db.py             # Database initialization command
├── payments.py             # Razorpay REST/signature helpers
├── products.py            # Catalogue, variants and inventory
├── seed.py                # Sample catalogue, category tree and coupon
├── webhook.py             # FastAPI Razorpay webhook endpoint
├── style.css              # A SQUARE visual system and responsive styles
├── assets/asquare-logo.svg # Brand logo artwork
├── sample_products.csv    # Sample catalogue reference data
├── tests/test_core.py     # Core tests
├── requirements.txt
├── .env.example
├── run_webhook.ps1
├── data/                  # Local SQLite database (created at runtime)
└── uploads/               # Reserved for future configured image storage
```

## Windows setup (PowerShell)

Python **3.13 is the recommended runtime** for this dependency set. Python 3.14 compatibility depends on compatible wheels being published by Streamlit, Pandas and their transitive dependencies. The project uses standard Python syntax and SQLite, but if `pip install` cannot resolve binary wheels on Python 3.14, use Python 3.13 rather than forcing a source build.

```powershell
# Go to the project directory
cd .\a_square

# Create and activate a virtual environment
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Create local environment settings
Copy-Item .env.example .env
notepad .env

# Initialize database and load sample products
python init_db.py

# Start the storefront
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`). If PowerShell blocks activation for the current session, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and activate again.

Set a strong, unique `ADMIN_PASSWORD` in `.env` before first launch. The first launch creates/promotes the configured `ADMIN_EMAIL` as an admin. Do not use the sample local credentials on a public deployment.

## Tests and checks

```powershell
python -m compileall -q .
python -m unittest discover -s tests -v
```

The test suite covers password hashing, registration/login, seeded category/product queries, totals, and checkout-signature verification. It does not replace a full browser, payment-provider, concurrency, or deployment test suite.

## Razorpay test mode

1. Create a Razorpay account and switch to **Test Mode**.
2. Put the Test Key ID and Key Secret in `.env` as `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
3. Restart the app. The backend creates Razorpay orders in INR paise.
4. Before enabling online payment in a customer-facing deployment, integrate the official Razorpay Checkout.js modal through a trusted Streamlit custom component/callback bridge. Pass the returned `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature` to a server-side endpoint that calls `checkout.confirm_razorpay(...)`. Never accept a browser redirect or client-side success flag as proof of payment.
5. Deploy the FastAPI webhook service over HTTPS and configure the Razorpay webhook URL as `https://YOUR_HOST/razorpay/webhook`. Set `RAZORPAY_WEBHOOK_SECRET` to the webhook secret and subscribe to `payment.captured`.
6. Test success, failure, duplicate webhook delivery, amount mismatch, and delayed payment cases before launch.

Run the webhook locally (for development only):

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn webhook:app --host 127.0.0.1 --port 8001
```

A public HTTPS tunnel or deployed HTTPS endpoint is required for Razorpay to reach a local webhook.

## Deployment path

- Deploy the Streamlit application on a host that supports Streamlit and persistent storage.
- Set environment variables in the host's secret manager; never upload `.env` or commit keys.
- Use HTTPS, secure server-side authentication/session handling, CSRF protection, rate limiting, account lockout, password reset tokens and audit logs before public launch.
- SQLite is intended for local/single-instance development. For production, migrate to PostgreSQL using Alembic or another migration tool; replace SQLite-specific seed statements with portable upserts and test transaction/locking behaviour.
- Store product images in a private managed object store (S3-compatible) and serve via controlled public/CDN URLs. Validate MIME type and size on upload.
- Deploy the webhook service separately or as a managed API service with HTTPS, durable logs and monitoring.
- Add backups, error monitoring, privacy/terms/refund policies, GST/tax and invoice rules, shipping integration, and operational support workflows before accepting orders.

## Security notes

- Passwords use PBKDF2-HMAC-SHA256 with per-user random salts.
- SQL queries use parameterized statements.
- Inventory is decremented inside a database transaction with a conditional stock check.
- Razorpay secrets are read from environment variables and never placed in browser JavaScript.
- Checkout signatures and webhook signatures are compared using constant-time comparison; payment status is fetched from Razorpay before the checkout confirmation helper marks an order paid.
- Streamlit session state is suitable for this local MVP but is not a substitute for hardened production session/authentication infrastructure.
- Prices are integer rupees; Razorpay amounts are integer paise.
