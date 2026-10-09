"""
Staff blueprint routes.
Handles kitchen queue board, rapid status advancement, QR code scanning, and pickup verification.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.extensions import db
from app.models import Order, OrderStatus, QueueEntry, QueueStatus, PaymentStatus
from app.auth.utils import staff_required
from app.services.queue_service import QueueService
from app.services.qr_service import QRService

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


@staff_bp.route('/dashboard')
@staff_required
def dashboard():
    """Kitchen and queue order board for food court staff."""
    status_filter = request.args.get('status')

    query = Order.query.order_by(Order.created_at.asc())

    if status_filter:
        query = query.filter(Order.status == status_filter)
    else:
        # Default: show active queue orders (Pending, Accepted, Preparing, Ready)
        query = query.filter(Order.status.in_(OrderStatus.ACTIVE_QUEUE))

    orders = query.all()

    # Metrics summary for top chips
    pending_count = Order.query.filter_by(status=OrderStatus.PENDING).count()
    accepted_count = Order.query.filter_by(status=OrderStatus.ACCEPTED).count()
    preparing_count = Order.query.filter_by(status=OrderStatus.PREPARING).count()
    ready_count = Order.query.filter_by(status=OrderStatus.READY).count()
    completed_today = Order.query.filter_by(status=OrderStatus.COMPLETED).count()

    return render_template(
        'staff/dashboard.html',
        orders=orders,
        status_filter=status_filter,
        pending_count=pending_count,
        accepted_count=accepted_count,
        preparing_count=preparing_count,
        ready_count=ready_count,
        completed_today=completed_today,
        OrderStatus=OrderStatus
    )


@staff_bp.route('/order/<int:order_id>/update-status', methods=['POST'])
@staff_required
def update_order_status(order_id):
    """Transition an order to the next kitchen / fulfillment status."""
    order = Order.query.get_or_404(order_id)
    target_status = request.form.get('target_status')

    if not target_status or target_status not in OrderStatus.ALL:
        flash("Invalid target status specified.", "danger")
        return redirect(url_for('staff.dashboard'))

    success, msg = QueueService.update_order_status(order, target_status, changed_by_role='staff')
    if success:
        flash(f"Order #{order.order_number} status updated to '{target_status}'.", "success")
    else:
        flash(msg, "danger")

    return redirect(url_for('staff.dashboard'))


@staff_bp.route('/verify', methods=['GET', 'POST'])
@staff_required
def verify_pickup():
    """
    Staff-side QR Code & Order verification page.
    Accepts scanned QR payload or manual Order Number input.
    """
    verified_order = None
    verification_error = None
    verification_success = None

    if request.method == 'POST':
        raw_input = (request.form.get('order_query') or '').strip()
        action = request.form.get('action')  # 'check' or 'confirm_pickup'
        order_id_to_complete = request.form.get('order_id')

        if action == 'confirm_pickup' and order_id_to_complete:
            order = Order.query.get(int(order_id_to_complete))
            if not order:
                flash("Order not found.", "danger")
                return redirect(url_for('staff.verify_pickup'))

            if order.status == OrderStatus.COMPLETED:
                flash(f"ALERT: Order #{order.order_number} was ALREADY collected on {order.completed_at.strftime('%I:%M %p') if order.completed_at else 'earlier'}! Duplicate pickup prevented.", "danger")
                return redirect(url_for('staff.verify_pickup'))

            # Complete the pickup
            success, msg = QueueService.update_order_status(order, OrderStatus.COMPLETED, changed_by_role='staff')
            if success:
                flash(f"Order #{order.order_number} verified and handed over successfully!", "success")
            else:
                flash(msg, "danger")
            return redirect(url_for('staff.verify_pickup'))

        if not raw_input:
            verification_error = "Please enter an order number or scan a QR code."
            return render_template('staff/verify.html', error=verification_error)

        parsed = QRService.parse_qr_payload(raw_input)
        order_num = parsed['order_number']
        token = parsed['token']

        order = Order.query.filter_by(order_number=order_num).first()
        if not order:
            verification_error = f"No order found matching '{order_num}'."
        else:
            # If token was supplied in QR, verify match
            if token and order.verification_token != token:
                verification_error = "Security alert: QR verification token is invalid or does not match."
            elif order.status == OrderStatus.COMPLETED:
                verification_error = f"Duplicate Pickup Warning: This order was already picked up on {order.completed_at.strftime('%Y-%m-%d %H:%M') if order.completed_at else 'earlier'}."
                verified_order = order
            elif order.status == OrderStatus.CANCELLED:
                verification_error = "Order was cancelled and cannot be fulfilled."
                verified_order = order
            else:
                verified_order = order

    return render_template(
        'staff/verify.html',
        verified_order=verified_order,
        error=verification_error,
        success=verification_success
    )
