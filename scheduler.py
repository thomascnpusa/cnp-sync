import schedule
import time
from app.shopify_sync import sync_sales

def run_sync():
    from app import create_app
    app = create_app()
    with app.app_context():
        print(f"Running scheduled sync at {time.ctime()}")
        sync_sales()

# Schedule sync every hour
schedule.every(1).hours.do(run_sync)

if __name__ == "__main__":
    print("Starting scheduler...")
    run_sync()  # Run once immediately for testing
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
