def load_bom(app):
    # Import db and models inside the function, after app is initialized
    from app import db
    from app.models import BillOfMaterials, Product

    # Sample BOM data
    sample_boms = [
        {"finished_product_id": "20001", "component_product_id": "110000", "quantity": 0.5},
        {"finished_product_id": "20001", "component_product_id": "110001", "quantity": 0.1},
        {"finished_product_id": "15012", "component_product_id": "110000", "quantity": 0.3},
    ]

    # Use db.session.get() for queries
    for bom in sample_boms:
        finished_product = db.session.get(Product, bom["finished_product_id"])
        component_product = db.session.get(Product, bom["component_product_id"])
        if not finished_product:
            print(f"Warning: Finished product {bom['finished_product_id']} not found in database")
            continue
        if not component_product:
            print(f"Warning: Component product {bom['component_product_id']} not found in database")
            continue

        # Check for existing BOM entry
        existing = BillOfMaterials.query.filter_by(
            finished_product_id=bom["finished_product_id"],
            component_product_id=bom["component_product_id"]
        ).first()
        if not existing:
            new_bom = BillOfMaterials(**bom)
            db.session.add(new_bom)
        else:
            print(f"BOM entry for {bom['finished_product_id']} -> {bom['component_product_id']} already exists")

    try:
        db.session.commit()
        print("BOM data loaded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error loading BOM data: {e}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        load_bom(app)  # Pass the app instance
