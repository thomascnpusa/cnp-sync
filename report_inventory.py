def report_inventory(app):
    from app import db
    from app.models import Inventory, Product, Sale
    from sqlalchemy import func
    from datetime import datetime, timedelta

    MAX_LOOKBACK_DAYS = 30
    LEAD_TIME_DAYS = 7

    with app.app_context():
        earliest_sale = db.session.query(func.min(Sale.date)).scalar()
        if earliest_sale:
            days_of_data = (datetime.now() - earliest_sale).days + 1
            lookback_days = min(MAX_LOOKBACK_DAYS, days_of_data)
        else:
            lookback_days = 1

        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        items = Inventory.query.all()
        
        # All inventory items
        inventory_data = []
        for item in items:
            product = Product.query.get(item.product_id)
            name = product.product_name if product else "Unknown"
            total_sold = db.session.query(func.sum(Sale.quantity)).filter(
                Sale.product_id == item.product_id,
                Sale.date >= cutoff_date
            ).scalar() or 0
            daily_sales_rate = total_sold / lookback_days
            forecasted_demand = daily_sales_rate * LEAD_TIME_DAYS
            inventory_data.append({
                'product_id': item.product_id,
                'name': name,
                'location': item.location,
                'quantity': item.quantity,
                'minimum': item.minimum_quantity,
                'forecasted_demand': forecasted_demand
            })

        # Low inventory items
        low_items = Inventory.query.filter(Inventory.quantity < Inventory.minimum_quantity).all()
        low_inventory_data = []
        for item in low_items:
            product = Product.query.get(item.product_id)
            name = product.product_name if product else "Unknown"
            total_sold = db.session.query(func.sum(Sale.quantity)).filter(
                Sale.product_id == item.product_id,
                Sale.date >= cutoff_date
            ).scalar() or 0
            daily_sales_rate = total_sold / lookback_days
            forecasted_demand = daily_sales_rate * LEAD_TIME_DAYS
            low_inventory_data.append({
                'product_id': item.product_id,
                'name': name,
                'quantity': item.quantity,
                'minimum': item.minimum_quantity,
                'forecasted_demand': forecasted_demand
            })

        return {
            'lookback_days': lookback_days,
            'inventory': inventory_data,
            'low_inventory': low_inventory_data
        }

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    result = report_inventory(app)
    # For testing in terminal
    print(f"Inventory Report (Based on {result['lookback_days']}-day lookback):")
    print("Product ID | Name                | Location      | Quantity | Minimum | Forecasted Demand")
    print("-" * 90)
    for item in result['inventory']:
        print(f"{item['product_id']:11} | {item['name']:19} | {item['location']:13} | {item['quantity']:8} | {item['minimum']:7} | {item['forecasted_demand']:16.2f}")
    if result['low_inventory']:
        print(f"\nLow Inventory Items (Below Minimum, {result['lookback_days']}-day lookback):")
        print("Product ID | Name                | Quantity | Minimum | Forecasted Demand")
        print("-" * 70)
        for item in result['low_inventory']:
            print(f"{item['product_id']:11} | {item['name']:19} | {item['quantity']:8} | {item['minimum']:7} | {item['forecasted_demand']:16.2f}")
