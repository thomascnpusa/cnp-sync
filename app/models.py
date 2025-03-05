from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Product(db.Model):
    product_id = db.Column(db.String(50), primary_key=True)
    product_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    sellable = db.Column(db.Boolean, default=True)
    default_unit_of_measure = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    instructions = db.Column(db.Text, nullable=True)

class Inventory(db.Model):
    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    location = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    minimum_quantity = db.Column(db.Float, nullable=False)
    batch_number = db.Column(db.String(255), nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    product = db.relationship('Product', backref='inventory')

class Sale(db.Model):
    sale_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    channel = db.Column(db.String(50), nullable=False)

class InventoryReceipt(db.Model):
    receipt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    quantity_received = db.Column(db.Float, nullable=False)
    date_received = db.Column(db.DateTime, default=db.func.now())
    batch_number = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.String(255), nullable=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # e.g., 'Manager', 'Operator'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class ProductionOrder(db.Model):
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    quantity_to_produce = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    date_submitted = db.Column(db.DateTime, default=db.func.now())
    date_fulfilled = db.Column(db.DateTime, nullable=True)
    production_batch = db.Column(db.String(50), unique=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    qa_signoff = db.Column(db.String(50), nullable=True)  # QA username or initials
    product = db.relationship('Product', backref='production_orders')
    operator = db.relationship('User', backref='production_orders')

class BillOfMaterials(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    finished_product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    component_product_id = db.Column(db.String(50), db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    product_finished = db.relationship('Product', foreign_keys=[finished_product_id], backref='bom_finished')
    product_component = db.relationship('Product', foreign_keys=[component_product_id], backref='bom_component')

class ProductionAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('production_order.order_id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., 'Submitted', 'Fulfilled', 'Edited'
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    details = db.Column(db.Text, nullable=True)  # e.g., 'Qty changed from 10 to 20'
    user = db.relationship('User', backref='audit_logs')