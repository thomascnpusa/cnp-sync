import csv
from app import db
from app.models import Product, Inventory, InventoryReceipt
from datetime import datetime

def import_inventory():
    with open('initial_inventory.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Add or update Product
            product = Product.query.get(row['product_id'])
            if not product:
                product = Product(
                    product_id=row['product_id'],
                    product_name=row['product_name'],
                    type=row['type'],
                    sellable=row['Sellable'].lower() == 'true',
                    default_unit_of_measure=row['default_unit_of_measure']
                )
                db.session.add(product)
            else:
                product.product_name = row['product_name']
                product.type = row['type']
                product.sellable = row['Sellable'].lower() == 'true'
                product.default_unit_of_measure = row['default_unit_of_measure']

            # Add or update Inventory
            inventory = Inventory.query.filter_by(product_id=row['product_id'], location=row['location']).first()
            if not inventory:
                inventory = Inventory(
                    product_id=row['product_id'],
                    location=row['location'],
                    quantity=float(row['quantity']),
                    minimum_quantity=float(row['minimum_quantity'])
                )
                db.session.add(inventory)
            else:
                inventory.quantity = float(row['quantity'])
                inventory.minimum_quantity = float(row['minimum_quantity'])

            # Add InventoryReceipt if batch_number exists
            if row['batch_number'] and row['batch_number'].lower() != 'none':
                receipt = InventoryReceipt(
                    product_id=row['product_id'],
                    quantity_received=float(row['quantity']),
                    date_received=datetime.utcnow(),
                    batch_number=row['batch_number'],
                    notes="Initial stock"
                )
                db.session.add(receipt)

        try:
            db.session.commit()
            print("Inventory imported successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing inventory: {e}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        import_inventory()
