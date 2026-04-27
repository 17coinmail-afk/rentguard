import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
PRICE_PER_PROPERTY = int(os.getenv("PRICE_PER_PROPERTY", "500"))
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

# Subscription periods in days
TRIAL_DAYS = 7
SUBSCRIPTION_DAYS = 30

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/rentguard.db")