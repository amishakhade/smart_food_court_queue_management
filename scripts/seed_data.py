"""
Database seeding script.
Populates initial food court categories, menu items, sample users, and operational settings.
Idempotent: safe to run multiple times without duplicating data.
"""
import sys
from pathlib import Path
from decimal import Decimal

# Ensure project root is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.extensions import db
from app.models import (
    User, UserRole, Category, MenuItem, ApplicationSetting,
    Order, OrderItem, OrderStatus, QueueEntry, QueueStatus, PaymentRecord, PaymentMethod, PaymentStatus
)


def seed_database():
    """Seed demo food court categories, menu items, users, and settings."""
    # 1. Operational settings
    settings = {
        'avg_preparation_time_mins': ('8', 'Average preparation time per order in minutes'),
        'cancellation_time_limit_mins': ('5', 'Allowed order cancellation window in minutes'),
        'food_court_name': ('Campus Smart Food Court', 'Branded name of the food court facility'),
        'is_ordering_open': ('1', '1 if ordering is open, 0 if closed for maintenance')
    }
    for k, (v, desc) in settings.items():
        if not ApplicationSetting.query.filter_by(key=k).first():
            db.session.add(ApplicationSetting(key=k, value=v, description=desc))

    # 2. Seed Default Accounts
    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@foodcourt.edu',
            full_name='Food Court Administrator',
            phone='9876543210',
            role=UserRole.ADMIN,
            is_active=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

    # Staff
    if not User.query.filter_by(username='staff').first():
        staff = User(
            username='staff',
            email='staff@foodcourt.edu',
            full_name='Kitchen Lead Ramesh',
            phone='9876543211',
            role=UserRole.STAFF,
            is_active=True
        )
        staff.set_password('Staff@123')
        db.session.add(staff)

    # Demo Student
    demo_student = User.query.filter_by(username='student').first()
    if not demo_student:
        demo_student = User(
            username='student',
            email='aarav.student@campus.edu',
            full_name='Aarav Sharma',
            phone='9876543212',
            role=UserRole.STUDENT,
            is_active=True
        )
        demo_student.set_password('Student@123')
        db.session.add(demo_student)

    db.session.commit()

    # 3. Seed Categories
    category_data = [
        {'name': 'Snacks', 'icon': 'bi-cup-hot', 'display_order': 1, 'desc': 'Quick bites, rolls, fries and samosas'},
        {'name': 'Meals', 'icon': 'bi-egg-fried', 'display_order': 2, 'desc': 'Wholesome thalis, biryanis, and rice combos'},
        {'name': 'Beverages', 'icon': 'bi-cup-straw', 'display_order': 3, 'desc': 'Refreshing juices, cold coffee, and hot tea'},
        {'name': 'Desserts', 'icon': 'bi-cake2', 'display_order': 4, 'desc': 'Sweet delights, pastries, and ice creams'},
        {'name': 'Breakfast', 'icon': 'bi-brightness-alt-high', 'display_order': 5, 'desc': 'Fresh dosas, idlis, and poha to start the day'}
    ]

    cat_map = {}
    for c_info in category_data:
        cat = Category.query.filter_by(name=c_info['name']).first()
        if not cat:
            cat = Category(
                name=c_info['name'],
                icon=c_info['icon'],
                display_order=c_info['display_order'],
                description=c_info['desc'],
                is_active=True
            )
            db.session.add(cat)
            db.session.flush()
        cat_map[c_info['name']] = cat

    # 4. Seed Menu Items
    menu_items_data = [
        # Snacks
        {
            'category': 'Snacks',
            'name': 'Crispy Veg Samosa (2 Pcs)',
            'price': Decimal('30.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Golden crisp pastry triangles filled with spiced potato and green peas, served with mint chutney.',
            'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Snacks',
            'name': 'Paneer Tikka Kathi Roll',
            'price': Decimal('95.00'),
            'prep_time': 10,
            'is_veg': True,
            'desc': 'Char-grilled cottage cheese cubes wrapped in flaky paratha with sliced onions and tangy sauces.',
            'image_url': '/static/images/menu/paneer_tikka_kathi_roll.jpg'
        },
        {
            'category': 'Snacks',
            'name': 'Cheesy Garlic Bread',
            'price': Decimal('85.00'),
            'prep_time': 10,
            'is_veg': True,
            'desc': 'Toasted French baguette slathered in garlic herb butter and melted mozzarella cheese.',
            'image_url': 'https://images.unsplash.com/photo-1619895092538-128341789043?w=600&auto=format&fit=crop&q=80'
        },

        # Meals
        {
            'category': 'Meals',
            'name': 'Deluxe Veg Thali',
            'price': Decimal('140.00'),
            'prep_time': 12,
            'is_veg': True,
            'desc': 'Paneer Butter Masala, Dal Makhani, Jeera Rice, 3 Butter Rotis, Salad, and Gulab Jamun.',
            'image_url': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Meals',
            'name': 'Dum Chicken Biryani',
            'price': Decimal('165.00'),
            'prep_time': 12,
            'is_veg': False,
            'desc': 'Fragrant basmati rice slow-cooked with tender marinated chicken and rich whole spices, served with raita.',
            'image_url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Meals',
            'name': 'Chole Bhature (2 Pcs)',
            'price': Decimal('95.00'),
            'prep_time': 10,
            'is_veg': True,
            'desc': 'Fluffy puffed bhaturas served with spicy Amritsari chickpea curry, pickled onions, and green chilli.',
            'image_url': '/static/images/menu/chole_bhature.jpg'
        },
        {
            'category': 'Meals',
            'name': 'Paneer Butter Masala Combo',
            'price': Decimal('130.00'),
            'prep_time': 12,
            'is_veg': True,
            'desc': 'Rich creamy tomato gravy with cottage cheese cubes served with 2 butter naans.',
            'image_url': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80'
        },

        # Beverages
        {
            'category': 'Beverages',
            'name': 'Campus Special Masala Chai',
            'price': Decimal('20.00'),
            'prep_time': 4,
            'is_veg': True,
            'desc': 'Brewed Indian milk tea infused with crushed ginger, cardamom, and clove spices.',
            'image_url': 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Beverages',
            'name': 'Cold Coffee with Chocolate Drizzle',
            'price': Decimal('60.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Chilled thick blended coffee with vanilla ice cream and Hershey chocolate syrup.',
            'image_url': 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Beverages',
            'name': 'Fresh Sweet Lime (Mosambi) Juice',
            'price': Decimal('50.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Freshly pressed sweet lime juice with black salt and chat masala seasoning.',
            'image_url': 'https://images.unsplash.com/photo-1613478223719-2ab802602423?w=600&auto=format&fit=crop&q=80'
        },
        {
            'category': 'Beverages',
            'name': 'Mango Lassi',
            'price': Decimal('55.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Traditional churned yoghurt smoothie blended with sweet Alphonso mango pulp.',
            'image_url': 'https://images.unsplash.com/photo-1546173159-315724a31696?w=600&auto=format&fit=crop&q=80'
        },

        # Desserts
        {
            'category': 'Desserts',
            'name': 'Hot Gulab Jamun (2 Pcs)',
            'price': Decimal('40.00'),
            'prep_time': 3,
            'is_veg': True,
            'desc': 'Soft milk solid dumplings deep-fried and soaked in warm fragrant cardamom sugar syrup.',
            'image_url': '/static/images/menu/hot_gulab_jamun.jpg'
        },
        {
            'category': 'Desserts',
            'name': 'Fudge Brownie with Vanilla Ice Cream',
            'price': Decimal('90.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Warm dark chocolate fudge brownie served with a scoop of vanilla ice cream.',
            'image_url': 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80'
        },

        # Breakfast
        {
            'category': 'Breakfast',
            'name': 'Crispy Masala Dosa',
            'price': Decimal('75.00'),
            'prep_time': 8,
            'is_veg': True,
            'desc': 'Thin golden rice crepe stuffed with spiced potato mash, served with coconut chutney & hot sambar.',
            'image_url': '/static/images/menu/crispy_masala_dosa.jpg'
        },
        {
            'category': 'Breakfast',
            'name': 'Indori Poha with Sev & Peanuts',
            'price': Decimal('40.00'),
            'prep_time': 5,
            'is_veg': True,
            'desc': 'Flattened rice tossed with turmeric, mustard seeds, onions, topped with crunchy ratlami sev.',
            'image_url': '/static/images/menu/indori_poha.jpg'
        }
    ]

    for item_data in menu_items_data:
        existing = MenuItem.query.filter_by(name=item_data['name']).first()
        if not existing:
            cat = cat_map.get(item_data['category'])
            if cat:
                menu_item = MenuItem(
                    category_id=cat.id,
                    name=item_data['name'],
                    price=item_data['price'],
                    preparation_time_mins=item_data['prep_time'],
                    is_veg=item_data['is_veg'],
                    description=item_data['desc'],
                    image_url=item_data['image_url'],
                    is_available=True
                )
                db.session.add(menu_item)

    # Correct image paths on already-seeded databases as well as new ones.
    image_fixes = {
        'Chole Bhature (2 Pcs)': '/static/images/menu/chole_bhature.jpg',
        'Crispy Masala Dosa': '/static/images/menu/crispy_masala_dosa.jpg',
        'Hot Gulab Jamun (2 Pcs)': '/static/images/menu/hot_gulab_jamun.jpg',
        'Indori Poha with Sev & Peanuts': '/static/images/menu/indori_poha.jpg',
        'Paneer Tikka Kathi Roll': '/static/images/menu/paneer_tikka_kathi_roll.jpg',
    }
    for item_name, image_path in image_fixes.items():
        item = MenuItem.query.filter_by(name=item_name).first()
        if item:
            item.image_url = image_path

    # Remove only this menu item. Existing order_items keep their historical
    # item_name/unit_price snapshot and their nullable foreign key.
    MenuItem.query.filter(MenuItem.name.ilike('%peri%peri%french%fries%')).delete(synchronize_session=False)

    db.session.commit()
    print("Database seeding completed successfully!")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_database()
