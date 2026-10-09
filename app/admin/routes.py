"""
Administrator blueprint routes.
Provides complete food court metrics, Chart.js analytics, menu CRUD,
category control, staff accounts, order history, and operational settings.
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from sqlalchemy import func, desc
from app.extensions import db
from app.models import User, UserRole, Category, MenuItem, Order, OrderItem, OrderStatus, PaymentRecord, PaymentStatus, QueueEntry, QueueStatus, ApplicationSetting
from app.auth.utils import admin_required
from app.services.queue_service import QueueService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Main administrative analytics dashboard with real-time MySQL statistics."""
    today_start = datetime.combine(date.today(), datetime.min.time())

    # 1. Database-calculated KPI counters
    total_orders = Order.query.count()
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    active_queue_count = Order.query.filter(Order.status.in_(OrderStatus.ACTIVE_QUEUE)).count()
    completed_orders = Order.query.filter_by(status=OrderStatus.COMPLETED).count()
    cancelled_orders = Order.query.filter_by(status=OrderStatus.CANCELLED).count()

    # Total Sales (calculated solely on completed orders)
    sales_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0))\
        .filter(Order.status == OrderStatus.COMPLETED).scalar()
    total_sales = float(sales_query or 0)

    # Today's Sales
    today_sales_query = db.session.query(func.coalesce(func.sum(Order.total_amount), 0))\
        .filter(Order.status == OrderStatus.COMPLETED, Order.created_at >= today_start).scalar()
    today_sales = float(today_sales_query or 0)

    # 2. Popular food items (top 5 by quantity ordered)
    popular_items = db.session.query(
        OrderItem.item_name,
        func.sum(OrderItem.quantity).label('total_qty'),
        func.sum(OrderItem.subtotal).label('total_rev')
    ).group_by(OrderItem.item_name)\
     .order_by(desc('total_qty'))\
     .limit(5)\
     .all()

    # 3. Recent Orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()

    # 4. Settings
    avg_prep = QueueService.get_avg_prep_time()

    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        today_orders=today_orders,
        active_queue_count=active_queue_count,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_sales=total_sales,
        today_sales=today_sales,
        popular_items=popular_items,
        recent_orders=recent_orders,
        avg_prep=avg_prep
    )


@admin_bp.route('/api/analytics')
@admin_required
def api_analytics():
    """Returns past 7 days order counts and sales for Chart.js."""
    labels = []
    order_counts = []
    daily_sales = []

    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_start = datetime.combine(d, datetime.min.time())
        d_end = datetime.combine(d, datetime.max.time())
        
        labels.append(d.strftime('%a, %d %b'))

        # Order count for this day
        cnt = Order.query.filter(Order.created_at >= d_start, Order.created_at <= d_end).count()
        order_counts.append(cnt)

        # Sales for this day (completed orders only)
        rev = db.session.query(func.coalesce(func.sum(Order.total_amount), 0))\
            .filter(Order.status == OrderStatus.COMPLETED, Order.created_at >= d_start, Order.created_at <= d_end)\
            .scalar()
        daily_sales.append(float(rev or 0))

    # Category breakdown
    cat_stats = db.session.query(
        Category.name,
        func.count(MenuItem.id)
    ).join(MenuItem, Category.id == MenuItem.category_id, isouter=True)\
     .group_by(Category.id, Category.name)\
     .all()

    category_labels = [c[0] for c in cat_stats]
    category_counts = [c[1] for c in cat_stats]

    return jsonify({
        'sales_labels': labels,
        'order_counts': order_counts,
        'daily_sales': daily_sales,
        'category_labels': category_labels,
        'category_counts': category_counts
    })


# ---------------- MENU MANAGEMENT ----------------

@admin_bp.route('/menu', methods=['GET', 'POST'])
@admin_required
def menu_management():
    """List and create menu items."""
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        description = (request.form.get('description') or '').strip()
        image_url = (request.form.get('image_url') or '').strip()
        prep_time = request.form.get('prep_time', 10)
        is_veg = request.form.get('is_veg') == '1'
        is_available = request.form.get('is_available') == '1'

        if not name or not category_id or not price:
            flash("Item name, category, and price are required.", "danger")
            return redirect(url_for('admin.menu_management'))

        try:
            price_dec = Decimal(price)
            if price_dec <= 0:
                raise ValueError()
        except Exception:
            flash("Please provide a valid positive price.", "danger")
            return redirect(url_for('admin.menu_management'))

        item = MenuItem(
            name=name,
            category_id=int(category_id),
            price=price_dec,
            description=description,
            image_url=image_url or None,
            preparation_time_mins=int(prep_time),
            is_veg=is_veg,
            is_available=is_available
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Menu item '{name}' added successfully!", "success")
        return redirect(url_for('admin.menu_management'))

    items = MenuItem.query.join(Category).order_by(Category.name.asc(), MenuItem.name.asc()).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name.asc()).all()
    return render_template('admin/menu.html', items=items, categories=categories)


@admin_bp.route('/menu/<int:item_id>/edit', methods=['POST'])
@admin_required
def edit_menu_item(item_id):
    """Edit existing menu item."""
    item = MenuItem.query.get_or_404(item_id)

    name = (request.form.get('name') or '').strip()
    category_id = request.form.get('category_id')
    price = request.form.get('price')
    description = (request.form.get('description') or '').strip()
    image_url = (request.form.get('image_url') or '').strip()
    prep_time = request.form.get('prep_time', 10)
    is_veg = request.form.get('is_veg') == '1'
    is_available = request.form.get('is_available') == '1'

    if not name or not category_id or not price:
        flash("Name, category, and price are required.", "danger")
        return redirect(url_for('admin.menu_management'))

    try:
        price_dec = Decimal(price)
    except Exception:
        flash("Invalid price value.", "danger")
        return redirect(url_for('admin.menu_management'))

    item.name = name
    item.category_id = int(category_id)
    item.price = price_dec
    item.description = description
    item.image_url = image_url or None
    item.preparation_time_mins = int(prep_time)
    item.is_veg = is_veg
    item.is_available = is_available
    item.updated_at = datetime.utcnow()

    db.session.commit()
    flash(f"Menu item '{item.name}' updated successfully.", "success")
    return redirect(url_for('admin.menu_management'))


@admin_bp.route('/menu/<int:item_id>/toggle-stock', methods=['POST'])
@admin_required
def toggle_stock(item_id):
    """Quick toggle availability status for a food item."""
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    item.updated_at = datetime.utcnow()
    db.session.commit()
    status_str = "Available" if item.is_available else "Out of Stock"
    flash(f"'{item.name}' is now marked as {status_str}.", "info")
    return redirect(url_for('admin.menu_management'))


@admin_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_menu_item(item_id):
    """Delete a menu item."""
    item = MenuItem.query.get_or_404(item_id)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Menu item '{name}' has been deleted.", "warning")
    return redirect(url_for('admin.menu_management'))


# ---------------- CATEGORY MANAGEMENT ----------------

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    """List and manage menu categories."""
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        icon = (request.form.get('icon') or 'bi-cup-hot').strip()
        display_order = request.form.get('display_order', 0)

        if not name:
            flash("Category name cannot be blank.", "danger")
            return redirect(url_for('admin.categories'))

        if Category.query.filter_by(name=name).first():
            flash(f"Category '{name}' already exists.", "danger")
            return redirect(url_for('admin.categories'))

        cat = Category(
            name=name,
            description=description,
            icon=icon,
            display_order=int(display_order or 0),
            is_active=True
        )
        db.session.add(cat)
        db.session.commit()
        flash(f"Category '{name}' created successfully.", "success")
        return redirect(url_for('admin.categories'))

    all_cats = Category.query.order_by(Category.display_order.asc(), Category.name.asc()).all()
    return render_template('admin/categories.html', categories=all_cats)


# ---------------- ORDER MANAGEMENT ----------------

@admin_bp.route('/orders')
@admin_required
def orders():
    """Comprehensive order and queue management page with search and status filters."""
    status_filter = request.args.get('status')
    search_query = (request.args.get('search') or '').strip()

    query = Order.query.order_by(Order.created_at.desc())

    if status_filter and status_filter in OrderStatus.ALL:
        query = query.filter(Order.status == status_filter)

    if search_query:
        query = query.filter(
            (Order.order_number.ilike(f"%{search_query}%")) |
            (Order.customer_name.ilike(f"%{search_query}%")) |
            (Order.customer_phone.ilike(f"%{search_query}%"))
        )

    all_orders = query.limit(100).all()

    return render_template(
        'admin/orders.html',
        orders=all_orders,
        status_filter=status_filter,
        search_query=search_query,
        OrderStatus=OrderStatus
    )


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Admin status update override."""
    order = Order.query.get_or_404(order_id)
    target_status = request.form.get('target_status')

    success, msg = QueueService.update_order_status(order, target_status, changed_by_role='admin')
    if success:
        flash(f"Order #{order.order_number} status updated to '{target_status}'.", "success")
    else:
        flash(msg, "danger")

    return redirect(url_for('admin.orders'))


# ---------------- USER & STAFF MANAGEMENT ----------------

@admin_bp.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    """Manage staff and view registered accounts."""
    if request.method == 'POST':
        full_name = (request.form.get('full_name') or '').strip()
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        phone = (request.form.get('phone') or '').strip()
        password = request.form.get('password') or ''
        role = request.form.get('role', UserRole.STAFF)

        if not full_name or not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('admin.users'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('admin.users'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for('admin.users'))

        user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"New {role} account '{username}' created successfully.", "success")
        return redirect(url_for('admin.users'))

    role_filter = request.args.get('role')
    query = User.query.order_by(User.created_at.desc())
    if role_filter in UserRole.CHOICES:
        query = query.filter_by(role=role_filter)

    all_users = query.all()
    return render_template('admin/users.html', users=all_users, role_filter=role_filter, UserRole=UserRole)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Toggle user active/inactive status."""
    user = User.query.get_or_404(user_id)
    if user.id == g.current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()
    state = "activated" if user.is_active else "deactivated"
    flash(f"User '{user.username}' has been {state}.", "info")
    return redirect(url_for('admin.users'))


# ---------------- SETTINGS ----------------

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Adjust average prep time, cancellation limit, and operational settings."""
    if request.method == 'POST':
        avg_prep = request.form.get('avg_preparation_time_mins', '8')
        court_name = request.form.get('food_court_name', 'Campus Smart Food Court')

        try:
            prep_int = int(avg_prep)
            if prep_int < 1:
                prep_int = 1
            ApplicationSetting.set_value('avg_preparation_time_mins', str(prep_int), 'Average preparation time in minutes')
            ApplicationSetting.set_value('food_court_name', court_name, 'Name of the food court')
            flash("System operational settings updated successfully.", "success")
        except Exception as e:
            flash(f"Failed to update settings: {str(e)}", "danger")

        return redirect(url_for('admin.settings'))

    avg_prep = QueueService.get_avg_prep_time()
    court_name = ApplicationSetting.get_value('food_court_name', 'Campus Smart Food Court')
    return render_template('admin/settings.html', avg_prep=avg_prep, court_name=court_name)
