"""
SQLAlchemy models for Smart Food Court & Queue Management System.
Normalized schema with full integrity, relationships, and auditing.
"""
from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class UserRole:
    STUDENT = 'student'
    STAFF = 'staff'
    ADMIN = 'admin'

    CHOICES = [STUDENT, STAFF, ADMIN]


class OrderStatus:
    PENDING = 'Pending'
    ACCEPTED = 'Accepted'
    PREPARING = 'Preparing'
    READY = 'Ready for Pickup'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'

    ALL = [PENDING, ACCEPTED, PREPARING, READY, COMPLETED, CANCELLED]
    ACTIVE_QUEUE = [PENDING, ACCEPTED, PREPARING, READY]


class QueueStatus:
    ACTIVE = 'Active'
    CALLED = 'Called'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'


class PaymentMethod:
    CASH = 'Cash on Pickup'
    UPI = 'Demo UPI'

    CHOICES = [CASH, UPI]


class PaymentStatus:
    PENDING = 'Pending'
    PAID = 'Paid'
    REFUNDED = 'Refunded'
    FAILED = 'Failed'


class User(db.Model):
    """User model supporting Student, Staff, and Administrator roles."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    orders = db.relationship('Order', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_staff(self):
        return self.role in [UserRole.STAFF, UserRole.ADMIN]

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Category(db.Model):
    """Food item category (e.g. Snacks, Meals, Beverages, Desserts)."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(60), default='bi-cup-hot', nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = db.relationship('MenuItem', back_populates='category', cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'display_order': self.display_order,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Category {self.name}>'


class MenuItem(db.Model):
    """Database-driven food menu items with price, stock, and preparation time."""
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    preparation_time_mins = db.Column(db.Integer, default=10, nullable=False)
    is_veg = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category = db.relationship('Category', back_populates='items')
    order_items = db.relationship('OrderItem', back_populates='menu_item', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'image_url': self.image_url,
            'is_available': self.is_available,
            'preparation_time_mins': self.preparation_time_mins,
            'is_veg': self.is_veg
        }

    def __repr__(self):
        return f'<MenuItem {self.name} (Rs. {self.price})>'


class Order(db.Model):
    """Customer order details, status lifecycle, and token verification."""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_number = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default=OrderStatus.PENDING, nullable=False, index=True)
    special_instructions = db.Column(db.Text, nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    verification_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    estimated_ready_time = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    queue_entry = db.relationship('QueueEntry', back_populates='order', uselist=False, cascade='all, delete-orphan')
    payment = db.relationship('PaymentRecord', back_populates='order', uselist=False, cascade='all, delete-orphan')

    @property
    def is_cancellable(self):
        """Order can be cancelled only if Pending and within cancellation window."""
        if self.status != OrderStatus.PENDING:
            return False
        # Fetch setting or default 5 mins
        elapsed_seconds = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed_seconds <= (5 * 60)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'item_count': self.item_count,
            'queue_number': self.queue_entry.queue_display if self.queue_entry else None,
            'payment_method': self.payment.payment_method if self.payment else 'N/A',
            'payment_status': self.payment.status if self.payment else 'N/A',
            'is_cancellable': self.is_cancellable
        }

    def __repr__(self):
        return f'<Order {self.order_number} ({self.status})>'


class OrderItem(db.Model):
    """Historical line item preservation with snapshot of purchased name & unit price."""
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id', ondelete='SET NULL'), nullable=True)
    item_name = db.Column(db.String(120), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.String(255), nullable=True)

    order = db.relationship('Order', back_populates='items')
    menu_item = db.relationship('MenuItem', back_populates='order_items')

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'unit_price': float(self.unit_price),
            'quantity': self.quantity,
            'subtotal': float(self.subtotal),
            'notes': self.notes
        }

    def __repr__(self):
        return f'<OrderItem {self.item_name} x{self.quantity}>'


class QueueEntry(db.Model):
    """Live queue entry with numbering, sequence, and status."""
    __tablename__ = 'queue_entries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    queue_number = db.Column(db.Integer, nullable=False, index=True)
    queue_display = db.Column(db.String(20), nullable=False)  # e.g. Q-101
    status = db.Column(db.String(30), default=QueueStatus.ACTIVE, nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    called_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship('Order', back_populates='queue_entry')

    def to_dict(self):
        return {
            'id': self.id,
            'queue_number': self.queue_number,
            'queue_display': self.queue_display,
            'status': self.status,
            'joined_at': self.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
            'order_number': self.order.order_number if self.order else ''
        }

    def __repr__(self):
        return f'<QueueEntry {self.queue_display} ({self.status})>'


class PaymentRecord(db.Model):
    """Payment record tracking method, amount, status, and mock transactions."""
    __tablename__ = 'payment_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), unique=True, nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default=PaymentStatus.PENDING, nullable=False)
    transaction_reference = db.Column(db.String(64), nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order = db.relationship('Order', back_populates='payment')

    def to_dict(self):
        return {
            'id': self.id,
            'payment_method': self.payment_method,
            'amount': float(self.amount),
            'status': self.status,
            'transaction_reference': self.transaction_reference,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }

    def __repr__(self):
        return f'<PaymentRecord {self.payment_method}: Rs. {self.amount} ({self.status})>'


class ApplicationSetting(db.Model):
    """Dynamic key-value settings for food court operations."""
    __tablename__ = 'application_settings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_value(cls, key, value, description=None):
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=str(value), description=description)
            db.session.add(setting)
        db.session.commit()
        return setting

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'
