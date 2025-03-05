from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    load_dotenv()  # Load .env variables
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://thomaspoole@localhost/cnp_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'Ilovecnpusa')  # Fallback for testing
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your-app-password')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', 'your-email@gmail.com')
    
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    from .models import Product, InventoryReceipt, Inventory, ProductionOrder, BillOfMaterials, User, ProductionAuditLog
    print("Models loaded:", Product, InventoryReceipt, Inventory, ProductionOrder, BillOfMaterials, User, ProductionAuditLog)
    from .routes import bp
    app.register_blueprint(bp)

    return app