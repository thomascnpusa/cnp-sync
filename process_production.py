def process_production_order(app, order_id):
    from app import db
    from app.models import ProductionOrder, BillOfMaterials, Inventory

    with app.app_context():
        # Fetch the production order
        order = db.session.get(ProductionOrder, order_id)
        if not order or order.status != "Pending":
            print(f"Order {order_id} not found or not pending")
            return

        # Get BOM for the finished product
        boms = BillOfMaterials.query.filter_by(finished_product_id=order.product_id).all()
        if not boms:
            print(f"No BOM found for product {order.product_id}")
            return

        # Check and deduct raw materials
        for bom in boms:
            component_inventory = Inventory.query.filter_by(
                product_id=bom.component_product_id, 
                location="Woods Cross"
            ).first()
            required_quantity = bom.quantity * order.quantity_to_produce
            if not component_inventory or component_inventory.quantity < required_quantity:
                print(f"Insufficient inventory for {bom.component_product_id}: need {required_quantity}, have {component_inventory.quantity if component_inventory else 0}")
                return
            component_inventory.quantity -= required_quantity
            print(f"Deducted {required_quantity} of {bom.component_product_id}: {component_inventory.quantity} remaining")

        # Add finished goods to inventory
        finished_inventory = Inventory.query.filter_by(
            product_id=order.product_id, 
            location="Woods Cross"
        ).first()
        if not finished_inventory:
            finished_inventory = Inventory(
                product_id=order.product_id,
                location="Woods Cross",
                quantity=order.quantity_to_produce,
                minimum_quantity=0
            )
            db.session.add(finished_inventory)
        else:
            finished_inventory.quantity += order.quantity_to_produce
        print(f"Added {order.quantity_to_produce} of {order.product_id} to inventory")

        # Update order status
        order.status = "Completed"

        try:
            db.session.commit()
            print(f"Production order {order_id} completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error processing order {order_id}: {e}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    # Process order ID 1 as an example (adjust based on your data)
    process_production_order(app, 1)
