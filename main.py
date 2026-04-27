import sys
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure data dir exists for SQLite
os.makedirs('data', exist_ok=True)

try:
    from bot.main import main
    import asyncio
    asyncio.run(main())
except Exception as e:
    logging.error("FATAL ERROR: " + str(e))
    traceback.print_exc()
    # Keep process alive so Render doesn't restart infinitely
    import time
    while True:
        time.sleep(60)
