from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request, Response
from flask_login import login_user, logout_user, login_required, current_user
from app import mail, db
from app.forms import ReceiveForm, ProduceForm, AdjustInventoryForm, ManualSaleForm, BOMForm, ProductDetailForm, FulfillForm, LoginForm
from flask_mail import Message
from app.models import Product, InventoryReceipt, Inventory, ProductionOrder, BillOfMaterials, Sale, User, ProductionAuditLog
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import uuid
import csv
import io
import contextlib
from app.shopify_sync import sync_sales

bp = Blueprint('main', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard', _external=True, _scheme='http') + '?nocache=' + str(int(datetime.now().timestamp())))
        flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('main.login'))

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    print("Dashboard route triggered!")
    low_stock = Inventory.query.filter(Inventory.quantity < Inventory.minimum_quantity).all()
    pending_orders = ProductionOrder.query.filter_by(status='Pending').order_by(ProductionOrder.is_rush.desc(), ProductionOrder.date_submitted).limit(5).all()
    cutoff_date = datetime.now() - timedelta(days=7)
    recent_sales_by_product = db.session.query(
        Sale.product_id,
        Product.product_name,
        func.sum(Sale.quantity).label('total_sold')
    ).join(Product).filter(Sale.date >= cutoff_date).group_by(Sale.product_id, Product.product_name).limit(5).all()
    total_inventory_value = db.session.query(func.sum(Inventory.quantity * Product.unit_cost)).join(Product).scalar() or 0
    orders_this_week = ProductionOrder.query.filter(ProductionOrder.date_submitted >= cutoff_date).count()
    sales_this_month = db.session.query(func.sum(Sale.quantity)).filter(Sale.date >= datetime.now() - timedelta(days=30)).scalar() or 0
    return render_template('dashboard.html', 
                         low_stock=low_stock, 
                         pending_orders=pending_orders, 
                         recent_sales_by_product=recent_sales_by_product,
                         total_inventory_value=total_inventory_value,
                         orders_this_week=orders_this_week,
                         sales_this_month=sales_this_month)

@bp.route('/sync')
@login_required
def sync():
    print("Sync route triggered!")
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        sync_sales()
    sync_output = output.getvalue()
    return render_template('sync.html', sync_output=sync_output)

@bp.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    from report_inventory import report_inventory
    print("Inventory report triggered!")
    report_data = report_inventory(current_app)
    
    page = request.args.get('page', 1, type=int)
    per_page = 25
    search_query = request.args.get('search', '')
    sellable_filter = request.args.get('sellable', 'all')
    sort_by = request.args.get('sort', 'product_id')
    sort_order = request.args.get('order', 'asc')
    
    query = Inventory.query.join(Product)
    if search_query:
        query = query.filter(or_(
            Product.product_id.ilike(f'%{search_query}%'),
            Product.product_name.ilike(f'%{search_query}%'),
            Inventory.batch_number.ilike(f'%{search_query}%')
        ))
    if sellable_filter == 'sellable':
        query = query.filter(Product.sellable == True)
    elif sellable_filter == 'non-sellable':
        query = query.filter(Product.sellable == False)
    
    if sort_by == 'quantity':
        order_column = Inventory.quantity
    elif sort_by == 'expiry_date':
        order_column = Inventory.expiry_date
    else:
        order_column = Product.product_id
    if sort_order == 'desc':
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    inventory_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    inventory_items = inventory_paginated.items
    
    if request.method == 'POST' and 'adjust_quantity' in request.form:
        inventory_id = request.form.get('inventory_id')
        adjust_quantity = float(request.form.get('adjust_quantity', 0))
        reason = request.form.get('reason', 'Manual adjustment')
        inventory = Inventory.query.get_or_404(inventory_id)
        new_quantity = inventory.quantity + adjust_quantity
        if new_quantity < 0:
            flash('Adjustment would result in negative inventory!', 'error')
        else:
            inventory.quantity = new_quantity
            db.session.commit()
            flash(f'Adjusted {inventory.product_ref.product_name} by {adjust_quantity} (New total: {new_quantity}). Reason: {reason}', 'success')
        return redirect(url_for('main.inventory', page=page, search=search_query, sellable=sellable_filter, sort=sort_by, order=sort_order))
    
    batch_history = {}
    for item in inventory_items:
        if item.batch_number:
            batches = item.batch_number.split(';')
            history = []
            for batch in batches:
                order = ProductionOrder.query.filter_by(production_batch=batch).first()
                if order:
                    history.append({
                        'batch': batch,
                        'order_id': order.order_id,
                        'product_id': order.product_id,
                        'quantity': order.quantity_to_produce,
                        'status': order.status,
                        'date': order.date_fulfilled or order.date_submitted
                    })
            batch_history[item.inventory_id] = history
    
    low_items = Inventory.query.filter(Inventory.quantity < Inventory.minimum_quantity).all()
    if low_items:
        msg = Message("Low Stock Alert", recipients=['your-email@gmail.com'])
        msg.body = "The following items are below minimum stock levels:\n\n"
        for item in low_items:
            msg.body += f"{item.product_ref.product_name} ({item.product_id}) at {item.location}: {item.quantity} (Min: {item.minimum_quantity})\n"
        try:
            mail.send(msg)
            print("Low stock alert email sent!")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    if 'export' in request.args:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product ID', 'Name', 'Location', 'Quantity', 'Min Qty', 'Batch Number', 'Expiry Date', 'Sellable'])
        for item in query.all():
            writer.writerow([
                item.product_id,
                item.product_ref.product_name,
                item.location,
                item.quantity,
                item.minimum_quantity,
                item.batch_number or 'N/A',
                item.expiry_date or 'N/A',
                'Yes' if item.product_ref.sellable else 'No'
            ])
        return Response(output.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=inventory.csv"})
    
    expiry_threshold = datetime.now() + timedelta(days=30)
    return render_template('inventory.html', 
                         lookback_days=report_data['lookback_days'],
                         inventory=inventory_items,
                         low_inventory=low_items,
                         pagination=inventory_paginated,
                         search_query=search_query,
                         sellable_filter=sellable_filter,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         expiry_threshold=expiry_threshold,
                         batch_history=batch_history)

@bp.route('/receive', methods=['GET', 'POST'])
@login_required
def receive():
    form = ReceiveForm()
    products = Product.query.all()
    for item_form in form.items:
        item_form.product.choices = [(p.product_id, f"{p.product_name} ({p.product_id}) - {p.default_unit_of_measure}") for p in products]
    if form.validate_on_submit():
        for item in form.items.data:
            if item['product'] and item['quantity']:
                expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d') if item['expiry_date'] else None
                receipt = InventoryReceipt(
                    product_id=item['product'],
                    quantity_received=item['quantity'],
                    batch_number=item['batch_number'],
                    date_received=expiry_date if expiry_date else db.func.now()
                )
                db.session.add(receipt)
                inventory = Inventory.query.filter_by(product_id=item['product'], location="Woods Cross").first()
                if inventory:
                    inventory.quantity += item['quantity']
                    inventory.batch_number = item['batch_number']
                    inventory.expiry_date = expiry_date
                else:
                    inventory = Inventory(
                        product_id=item['product'],
                        location="Woods Cross",
                        quantity=item['quantity'],
                        minimum_quantity=0,
                        batch_number=item['batch_number'],
                        expiry_date=expiry_date
                    )
                    db.session.add(inventory)
        db.session.commit()
        flash('Inventory received successfully!', 'success')
        return redirect(url_for('main.receive'))
    return render_template('receive.html', form=form)

@bp.route('/produce', methods=['GET', 'POST'])
@login_required
def produce():
    form = ProduceForm()
    products = Product.query.filter_by(sellable=True).all()
    form.product.choices = [(p.product_id, f"{p.product_name} ({p.product_id}) - {p.default_unit_of_measure}") for p in products]
    if form.validate_on_submit():
        batch = f"PROD-{uuid.uuid4().hex[:8]}"
        order = ProductionOrder(
            product_id=form.product.data,
            quantity_to_produce=form.quantity.data,
            status='Pending',
            date_submitted=db.func.now(),
            production_batch=batch,
            notes=form.notes.data,
            is_rush=form.is_rush.data
        )
        db.session.add(order)
        db.session.flush()
        audit = ProductionAuditLog(
            order_id=order.order_id,
            action='Submitted',
            details=f"New {'rush ' if order.is_rush else ''}order for {form.quantity.data} {form.product.data}"
        )
        db.session.add(audit)
        db.session.commit()
        flash(f"Production order {order.order_id} (Batch: {batch}) submitted successfully!{' (Rush)' if order.is_rush else ''}", 'success')
        return redirect(url_for('main.produce'))
    return render_template('produce.html', form=form, products=products)

@bp.route('/fulfill', methods=['GET', 'POST'])
@login_required
def fulfill():
    form = FulfillForm()
    if form.validate_on_submit():
        order_id = form.order_id.data
        order = ProductionOrder.query.get_or_404(order_id)
        if order.status == 'Pending':
            bom_items = BillOfMaterials.query.filter_by(finished_product_id=order.product_id).all()
            insufficient_stock = False
            for item in bom_items:
                required_quantity = item.quantity * order.quantity_to_produce
                inventory = Inventory.query.filter_by(product_id=item.component_product_id, location="Woods Cross").first()
                if not inventory or inventory.quantity < required_quantity:
                    insufficient_stock = True
                    flash(f"Insufficient stock for {item.component_product.product_name} (Required: {required_quantity}, Available: {inventory.quantity if inventory else 0})", 'error')
                    break
            
            if not insufficient_stock:
                for item in bom_items:
                    required_quantity = item.quantity * order.quantity_to_produce
                    inventory = Inventory.query.filter_by(product_id=item.component_product_id, location="Woods Cross").first()
                    inventory.quantity -= required_quantity
                    if inventory.batch_number:
                        inventory.batch_number += f";{order.production_batch}"
                    else:
                        inventory.batch_number = order.production_batch
                    db.session.add(inventory)
                    if inventory.quantity < inventory.minimum_quantity or inventory.quantity < 100:
                        flash(f"Warning: {item.component_product.product_name} stock is low ({inventory.quantity} remaining)", 'warning')
                
                finished_inventory = Inventory.query.filter_by(product_id=order.product_id, location="Woods Cross").first()
                if finished_inventory:
                    finished_inventory.quantity += order.quantity_to_produce
                    finished_inventory.batch_number = order.production_batch
                else:
                    finished_inventory = Inventory(
                        product_id=order.product_id,
                        location="Woods Cross",
                        quantity=order.quantity_to_produce,
                        minimum_quantity=0,
                        batch_number=order.production_batch
                    )
                db.session.add(finished_inventory)
                
                order.status = 'Fulfilled'
                order.date_fulfilled = db.func.now()
                db.session.flush()
                audit = ProductionAuditLog(
                    order_id=order.order_id,
                    action='Fulfilled',
                    details=f"Fulfilled {order.quantity_to_produce} units"
                )
                db.session.add(audit)
                db.session.commit()
                flash(f"Order {order_id} (Batch: {order.production_batch}) fulfilled and inventory updated!", 'success')
            else:
                db.session.rollback()
        else:
            flash(f"Order {order_id} is already fulfilled.", 'warning')
        return redirect(url_for('main.fulfill'))

    pending_orders = ProductionOrder.query.filter_by(status='Pending').order_by(ProductionOrder.is_rush.desc(), ProductionOrder.date_submitted).all()
    steps = [
        "1. Gather components from inventory.",
        "2. Measure and mix according to BOM quantities.",
        "3. Package the finished product.",
        "4. Update inventory with completed goods."
    ]
    return render_template('fulfill.html', orders=pending_orders, steps=steps, form=form)

@bp.route('/adjust', methods=['GET', 'POST'])
@login_required
def adjust():
    print("Adjust inventory route triggered!")
    form = AdjustInventoryForm()
    products = Product.query.all()
    form.product.choices = [(p.product_id, f"{p.product_name} ({p.product_id})") for p in products]
    
    product_id = request.args.get('product_id')
    if product_id and request.method == 'GET':
        form.product.data = product_id
    
    if form.validate_on_submit():
        inventory = Inventory.query.filter_by(product_id=form.product.data, location="Woods Cross").first()
        if inventory:
            inventory.quantity += form.quantity.data
            if inventory.quantity < 0:
                flash('Adjustment would result in negative inventory!', 'error')
                db.session.rollback()
            else:
                db.session.commit()
                flash(f'Inventory adjusted successfully! Reason: {form.reason.data}', 'success')
        else:
            if form.quantity.data < 0:
                flash('Cannot subtract from non-existent inventory!', 'error')
            else:
                inventory = Inventory(
                    product_id=form.product.data,
                    location="Woods Cross",
                    quantity=form.quantity.data,
                    minimum_quantity=0
                )
                db.session.add(inventory)
                db.session.commit()
                flash(f'Inventory created and adjusted successfully! Reason: {form.reason.data}', 'success')
        return redirect(url_for('main.adjust'))
    return render_template('adjust.html', form=form)

@bp.route('/sales', methods=['GET'])
@login_required
def sales():
    print("Sales dashboard triggered!")
    sales_by_product = db.session.query(
        Sale.product_id,
        Product.product_name,
        func.sum(Sale.quantity).label('total_sold')
    ).join(Product).group_by(Sale.product_id, Product.product_name).all()
    sales_by_channel = db.session.query(
        Sale.channel,
        func.sum(Sale.quantity).label('total_sold')
    ).group_by(Sale.channel).all()
    return render_template('sales.html', sales_by_product=sales_by_product, sales_by_channel=sales_by_channel)

@bp.route('/manual-sale', methods=['GET', 'POST'])
@login_required
def manual_sale():
    print("Manual sale route triggered!")
    form = ManualSaleForm()
    products = Product.query.filter_by(sellable=True).all()
    form.product.choices = [(p.product_id, f"{p.product_name} ({p.product_id})") for p in products]
    if form.validate_on_submit():
        inventory = Inventory.query.filter_by(product_id=form.product.data, location="Woods Cross").first()
        if inventory and inventory.quantity >= form.quantity.data:
            sale = Sale(
                order_id=f"MANUAL-{int(db.func.now().timestamp())}",
                date=db.func.now(),
                product_id=form.product.data,
                quantity=form.quantity.data,
                channel=form.channel.data
            )
            inventory.quantity -= form.quantity.data
            db.session.add(sale)
            db.session.commit()
            flash('Manual sale recorded successfully!', 'success')
        else:
            flash('Insufficient inventory for this sale!', 'error')
        return redirect(url_for('main.manual_sale'))
    return render_template('manual_sale.html', form=form)

@bp.route('/product/<product_id>', methods=['GET', 'POST'])
@login_required
def product_detail(product_id):
    print("Product detail route triggered for:", product_id)
    product = Product.query.get_or_404(product_id)
    bom_form = BOMForm()
    notes_form = ProductDetailForm(obj=product)
    component_products = Product.query.filter_by(sellable=False).all()
    for item_form in bom_form.items:
        item_form.component_product.choices = [(p.product_id, f"{p.product_name} ({p.product_id}) - {p.default_unit_of_measure}") for p in component_products]

    if request.method == 'POST':
        if 'bom_submit' in request.form and bom_form.validate():
            print("BOM form submitted with data:", request.form)
            for item in bom_form.items.data:
                if item['component_product'] and item['quantity']:
                    bom = BillOfMaterials(
                        finished_product_id=product_id,
                        component_product_id=item['component_product'],
                        quantity=item['quantity']
                    )
                    db.session.add(bom)
            db.session.commit()
            flash('BOM items added successfully!', 'success')
            return redirect(url_for('main.product_detail', product_id=product_id))
        elif 'notes_submit' in request.form and notes_form.validate():
            print("Notes form submitted with data:", request.form)
            product.notes = notes_form.notes.data
            product.instructions = notes_form.instructions.data
            product.unit_cost = notes_form.unit_cost.data
            db.session.commit()
            flash('Product details updated successfully!', 'success')
            return redirect(url_for('main.product_detail', product_id=product_id))

    inventory = Inventory.query.filter_by(product_id=product_id).all()
    sales_total = db.session.query(Sale.product_id, func.sum(Sale.quantity).label('total_sold')).filter_by(product_id=product_id).group_by(Sale.product_id).first()
    sales_by_channel = db.session.query(
        Sale.channel,
        func.sum(Sale.quantity).label('total_sold')
    ).filter_by(product_id=product_id).group_by(Sale.channel).all()
    production_orders = ProductionOrder.query.filter_by(product_id=product_id).order_by(ProductionOrder.date_submitted.desc()).all()
    bom_items = BillOfMaterials.query.filter_by(finished_product_id=product_id).all()
    return render_template('product_detail.html', product=product, bom_form=bom_form, notes_form=notes_form, 
                         inventory=inventory, sales_total=sales_total, sales_by_channel=sales_by_channel, 
                         production_orders=production_orders, bom_items=bom_items)

@bp.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    print("History route triggered!")
    status_filter = request.args.get('status', 'All')
    product_filter = request.args.get('product', '')
    batch_filter = request.args.get('batch', '')
    
    query = ProductionOrder.query
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    if product_filter:
        query = query.filter(ProductionOrder.product_id.ilike(f'%{product_filter}%'))
    if batch_filter:
        query = query.filter(ProductionOrder.production_batch.ilike(f'%{batch_filter}%'))
    
    orders = query.order_by(ProductionOrder.date_submitted.desc()).all()
    return render_template('history.html', orders=orders, status_filter=status_filter, product_filter=product_filter, batch_filter=batch_filter)

@bp.route('/history/<order_id>', methods=['GET', 'POST'])
@login_required
def order_detail(order_id):
    print(f"Order detail route triggered for order_id: {order_id}")
    order = ProductionOrder.query.get_or_404(order_id)
    bom_items = BillOfMaterials.query.filter_by(finished_product_id=order.product_id).all()
    audit_logs = ProductionAuditLog.query.filter_by(order_id=order_id).order_by(ProductionAuditLog.timestamp).all()
    
    form = ProduceForm(obj=order)
    form.product.choices = [(p.product_id, f"{p.product_name} ({p.product_id}) - {p.default_unit_of_measure}") for p in Product.query.filter_by(sellable=True).all()]
    
    if request.method == 'POST':
        if form.validate_on_submit() and order.status == 'Pending':
            old_qty = order.quantity_to_produce
            order.quantity_to_produce = form.quantity.data
            order.notes = form.notes.data
            audit = ProductionAuditLog(
                order_id=order.order_id,
                action='Edited',
                details=f"Qty changed from {old_qty} to {form.quantity.data}, notes updated"
            )
            db.session.add(audit)
            db.session.commit()
            flash(f"Order {order_id} updated successfully!", 'success')
        return redirect(url_for('main.order_detail', order_id=order_id))
    
    component_inventories = []
    for item in bom_items:
        inv = Inventory.query.filter_by(product_id=item.component_product_id, location="Woods Cross").first()
        if inv:
            required_qty = item.quantity * order.quantity_to_produce
            component_inventories.append({
                'product_id': item.component_product_id,
                'name': item.component_product.product_name,
                'batch_number': inv.batch_number,
                'current_quantity': inv.quantity,
                'used_quantity': required_qty if order.status == 'Fulfilled' else 0,
                'before_quantity': inv.quantity + required_qty if order.status == 'Fulfilled' else inv.quantity
            })
    
    finished_inventory = Inventory.query.filter_by(product_id=order.product_id, location="Woods Cross").first()
    finished_before = (finished_inventory.quantity - order.quantity_to_produce) if finished_inventory and order.status == 'Fulfilled' else 0
    
    return render_template('order_detail.html', order=order, bom_items=bom_items, 
                         component_inventories=component_inventories, 
                         finished_inventory=finished_inventory, finished_before=finished_before,
                         form=form, audit_logs=audit_logs)