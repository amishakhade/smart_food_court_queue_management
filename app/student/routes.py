"""
Student / Customer blueprint routes.
Covers browsing, searching, cart, checkout, confirmation, live tracking, and cancellation.
"""
import json
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, g
from app.extensions import db
from app.models import Category, MenuItem, Order, OrderStatus, PaymentMethod, PaymentStatus, UserRole
from app.auth.utils import login_required
from app.services.order_service import OrderService
from app.services.queue_service import QueueService

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def home():
    """Food court landing page with branding, featured categories, and live queue snapshot."""
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc()).all()
    featured_items = MenuItem.query.filter_by(is_available=True).limit(6).all()
    queue_board = QueueService.get_live_queue_board()
    
    # Active orders count
    active_count = Order.query.filter(Order.status.in_(OrderStatus.ACTIVE_QUEUE)).count()

    return render_template(
        'home.html',
        categories=categories,
        featured_items=featured_items,
        active_count=active_count,
        queue_board=queue_board[:5]
    )


@student_bp.route('/menu')
def menu():
    """Browse menu items with search, category filtering, and stock availability."""
    search_query = (request.args.get('search') or '').strip()
    category_id = request.args.get('category')
    veg_filter = request.args.get('veg')

    query = MenuItem.query.join(Category).filter(Category.is_active == True)

    if search_query:
        query = query.filter(
            (MenuItem.name.ilike(f"%{search_query}%")) |
            (MenuItem.description.ilike(f"%{search_query}%"))
        )

    if category_id and category_id.isdigit():
        query = query.filter(MenuItem.category_id == int(category_id))

    if veg_filter == '1':
        query = query.filter(MenuItem.is_veg == True)
    elif veg_filter == '0':
        query = query.filter(MenuItem.is_veg == False)

    menu_items = query.order_by(MenuItem.is_available.desc(), MenuItem.name.asc()).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order.asc()).all()

    return render_template(
        'menu.html',
        menu_items=menu_items,
        categories=categories,
        selected_category=int(category_id) if category_id and category_id.isdigit() else None,
        search_query=search_query,
        veg_filter=veg_filter
    )


@student_bp.route('/cart')
def cart():
    """Shopping cart view."""
    return render_template('cart.html')


@student_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page: takes customer details and processes order creation."""
    if request.method == 'POST':
        # Cart data passed via form JSON field or parsed
        cart_data_raw = request.form.get('cart_data', '[]')
        try:
            cart_items = json.loads(cart_data_raw)
        except Exception:
            cart_items = []

        if not cart_items:
            flash("Your cart is empty. Please add items before checking out.", "warning")
            return redirect(url_for('student.menu'))

        customer_data = {
            'name': request.form.get('name'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'special_instructions': request.form.get('special_instructions')
        }

        payment_data = {
            'payment_method': request.form.get('payment_method', PaymentMethod.CASH)
        }

        # Create order atomically
        success, result = OrderService.create_order(
            customer_data=customer_data,
            cart_items=cart_items,
            payment_data=payment_data,
            user=g.current_user if g.current_user else None
        )

        if not success:
            flash(result, "danger")
            return redirect(url_for('student.cart'))

        order = result
        flash(f"Order #{order.order_number} placed successfully!", "success")
        return redirect(url_for('student.order_confirmation', order_number=order.order_number))

    return render_template('checkout.html')


@student_bp.route('/order/<order_number>/confirmation')
def order_confirmation(order_number):
    """Order confirmation and QR code display page."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    position, wait_mins = QueueService.get_queue_position(order.id)
    return render_template(
        'order_confirmation.html',
        order=order,
        position=position,
        estimated_wait_mins=wait_mins
    )


@student_bp.route('/order/<order_number>/track')
def track_order(order_number):
    """Live-refreshing order tracking page."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    position, wait_mins = QueueService.get_queue_position(order.id)
    return render_template(
        'track_order.html',
        order=order,
        position=position,
        estimated_wait_mins=wait_mins
    )


@student_bp.route('/order/<order_number>/cancel', methods=['POST'])
def cancel_order(order_number):
    """Cancel order if it is still within the allowable Pending window."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # If student is logged in and not owner, restrict
    if g.current_user and order.user_id and order.user_id != g.current_user.id and not g.current_user.is_staff:
        flash("You are not authorized to cancel this order.", "danger")
        return redirect(url_for('student.track_order', order_number=order_number))

    success, msg = QueueService.update_order_status(order, OrderStatus.CANCELLED, changed_by_role='student')
    if success:
        flash("Your order has been cancelled successfully.", "info")
    else:
        flash(msg, "danger")

    return redirect(url_for('student.track_order', order_number=order_number))


@student_bp.route('/student/orders')
@login_required
def order_history():
    """Display past and active orders for logged in student."""
    orders = Order.query.filter_by(user_id=g.current_user.id)\
        .order_by(Order.created_at.desc())\
        .all()
    return render_template('order_history.html', orders=orders)


@student_bp.route('/queue')
def live_queue():
    """Public live queue board displaying active orders being prepared and called."""
    queue_board = QueueService.get_live_queue_board()
    avg_prep = QueueService.get_avg_prep_time()
    return render_template('queue_board.html', queue_board=queue_board, avg_prep=avg_prep)


# API endpoint for live order polling
@student_bp.route('/api/orders/<order_number>/status')
def api_order_status(order_number):
    """JSON API endpoint for periodic polling from the track_order page."""
    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    position, wait_mins = QueueService.get_queue_position(order.id)
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'status': order.status,
        'queue_display': order.queue_entry.queue_display if order.queue_entry else '',
        'queue_position': position,
        'estimated_wait_mins': wait_mins,
        'is_cancellable': order.is_cancellable,
        'is_ready': order.status == OrderStatus.READY,
        'is_completed': order.status == OrderStatus.COMPLETED,
        'is_cancelled': order.status == OrderStatus.CANCELLED
    })
