import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import sys

# Add the parent directory to the Python path for standalone runs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

STORES = {
    "CNP Pet": ("https://complete-natural-products.myshopify.com/admin/api/2023-10/orders.json", os.getenv("CNP_PET_TOKEN")),
    "CNPUSA": ("https://cnpusa.myshopify.com/admin/api/2023-10/orders.json", os.getenv("CNPUSA_TOKEN")),
    "CNPUSA Wholesale": ("https://cnpusa-wholesale.myshopify.com/admin/api/2023-10/orders.json", os.getenv("CNPUSA_WHOLESALE_TOKEN")),
}

def sync_sales():
    from app import db
    from app.models import Sale, Inventory, Product, ProductionOrder
    from sqlalchemy import func

    MAX_LOOKBACK_DAYS = 30
    LEAD_TIME_DAYS = 7
    BATCH_SIZE = 10

    since_time = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
    existing_ids = {sale.order_id for sale in Sale.query.all()}
    print(f"Existing order IDs: {existing_ids}")

    for store_name, (url, token) in STORES.items():
        headers = {"X-Shopify-Access-Token": token}
        params = {"status": "any", "updated_at_min": since_time}
        response = requests.get(url, headers=headers, params=params)
        print(f"{store_name} response status: {response.status_code}")

        if response.status_code == 200:
            orders = response.json().get("orders", [])
            print(f"{store_name} found {len(orders)} orders")
            for order in orders:
                order_id = order["name"]
                if order_id not in existing_ids:
                    for item in order["line_items"]:
                        sku = item.get("sku")
                        if not sku or sku == "N/A":
                            print(f"Skipping item in order {order_id}: No SKU")
                            continue
                        quantity = int(item["quantity"])
                        product = Product.query.get(sku)
                        if not product:
                            print(f"Product {sku} not found in database for order {order_id}")
                            continue

                        if product.sellable:
                            sale = Sale(
                                order_id=order_id,
                                date=datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")),
                                product_id=sku,
                                quantity=quantity,
                                channel=store_name
                            )
                            db.session.add(sale)

                            inventory = Inventory.query.filter_by(product_id=sku, location="Woods Cross").first()
                            if inventory:
                                if inventory.quantity >= quantity:
                                    inventory.quantity -= quantity
                                    print(f"Deducted {quantity} from {sku}: {inventory.quantity} remaining")
                                else:
                                    print(f"Insufficient stock for {sku}: {inventory.quantity} available, {quantity} needed")
                            else:
                                print(f"No inventory found for {sku} in Woods Cross")

            try:
                db.session.commit()
                print(f"Synced sales for {store_name}")
            except Exception as e:
                db.session.rollback()
                print(f"Error syncing {store_name}: {e}")

    earliest_sale = db.session.query(func.min(Sale.date)).scalar()
    if earliest_sale:
        days_of_data = (datetime.now() - earliest_sale).days + 1
        lookback_days = min(MAX_LOOKBACK_DAYS, days_of_data)
    else:
        lookback_days = 1

    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    sales_summary = db.session.query(
        Sale.product_id,
        func.sum(Sale.quantity).label('total_sold')
    ).filter(Sale.date >= cutoff_date).group_by(Sale.product_id).all()

    print(f"Forecasting with {lookback_days}-day lookback:")
    for product_id, total_sold in sales_summary:
        inventory = Inventory.query.filter_by(product_id=product_id, location="Woods Cross").first()
        if not inventory:
            print(f"No inventory for {product_id}")
            continue

        daily_sales_rate = total_sold / lookback_days
        forecasted_demand = daily_sales_rate * LEAD_TIME_DAYS
        reorder_threshold = forecasted_demand + inventory.minimum_quantity
        print(f"{product_id}: total_sold={total_sold}, daily_rate={daily_sales_rate:.2f}, forecast={forecasted_demand:.2f}, threshold={reorder_threshold:.2f}, current={inventory.quantity}")

        if inventory.quantity < reorder_threshold:
            existing_order = ProductionOrder.query.filter_by(
                product_id=product_id,
                status="Pending"
            ).first()
            if not existing_order:
                production_quantity = max(BATCH_SIZE, int(forecasted_demand + 0.99))
                new_order = ProductionOrder(
                    product_id=product_id,
                    quantity_to_produce=production_quantity,
                    status="Pending"
                )
                db.session.add(new_order)
                print(f"Created production order for {product_id}: {production_quantity} units (forecasted demand: {forecasted_demand:.2f})")
            else:
                print(f"Pending order exists for {product_id}")
        else:
            print(f"No order needed for {product_id}: quantity above threshold")

    try:
        db.session.commit()
        print("Production orders triggered successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error triggering production orders: {e}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        sync_sales()