# 🍔 Smart Food Court and Queue Management System

A production-ready, full-stack responsive web application designed for college food courts and student cafeterias. Built with **Python Flask**, **MySQL**, **Bootstrap 5**, **Chart.js**, and Python **QRCode**.

The system eliminates crowded cafeteria lines and chaos through digital self-ordering, real-time token tracking, dynamic waiting-time estimation, and contactless QR-verified meal pickup.

---

## 🌟 Key Features

### 1. 🎓 Student / Customer Module
- **Public Browsing:** Explore 16+ dishes across Categories (*Snacks, Meals, Beverages, Desserts, Breakfast*) without requiring prior login.
- **Dynamic Search & Filters:** Search food items by keyword, filter by category tabs, and toggle Vegetarian / Non-Vegetarian diet options.
- **Client-Side Cart with Instant Feedback:** Add items, adjust quantities, view real-time subtotals, and experience toast notifications.
- **Express Checkout:** Enter student name and phone number; select payment method (**Cash on Pickup** or **Demo UPI** simulation).
- **Server-Side Price Validation:** Every item availability and price calculation is verified on the backend to prevent tampering.
- **Unique Order & Token Generation:** Each order receives a human-readable identifier (e.g. `ORD-20261009-8472`) and daily queue token (`Q-101`, `Q-102`...).
- **Instant QR Code Generation:** Secure tokenized QR code generated using Python `qrcode` library (contains no sensitive personal data). Students can view and download their pickup pass.
- **Live Auto-Refreshing Order Tracker:** Tracks lifecycle progress (`Placed` ➔ `Accepted` ➔ `Cooking` ➔ `Ready for Pickup` ➔ `Completed`) with real-time status polling every 5 seconds.
- **Dynamic Queue Position & Waiting Time:** Displays live position in kitchen queue (e.g., `#2 in line`) and estimated prep time (`Queue Position × Avg Prep Time`).
- **Eligible Order Cancellation:** Students can cancel orders while still `Pending` within the 5-minute allowable window.
- **Student History:** View previous orders, timestamps, items, and receipts when signed in.

### 2. 👨‍🍳 Kitchen Staff Module
- **Kitchen Queue Display (KDS):** Visual order board highlighting incoming orders, cooking tickets, and pickup calls.
- **Rapid Status Advancement:** One-click status triggers:
  - `Accept Order` (Pending ➔ Accepted)
  - `Start Cooking` (Accepted ➔ Preparing)
  - `Mark Ready for Pickup` (Preparing ➔ Ready for Pickup)
  - `Complete Handover` (Ready for Pickup ➔ Completed)
- **Counter QR Pickup Verification:**
  - Built-in HTML5 camera QR scanner and manual order reference fallback.
  - Verifies cryptographic token matching against server.
  - Automatically updates cash payment status to `PAID` upon food handover.
  - **Duplicate Collection Prevention:** Re-scanning an already collected meal triggers a strict warning alert and blocks duplicate handover.

### 3. 📊 Food Court Administrator Module
- **Real-Time Analytics Dashboard:**
  - Total Revenue & Today's Sales (calculated exclusively on completed orders).
  - Total Orders, Today's Order Count, and Active Queue counter.
  - 7-Day Daily Orders and Sales Chart using **Chart.js**.
  - Category distribution doughnut chart.
  - Top Selling food items by units sold and revenue generated.
  - Recent transactions overview.
- **Database Menu CRUD:** Add, edit, and delete food items with prices, prep times, veg flags, and image links.
- **Live Stock Availability Toggle:** Instantly disable sold-out dishes. Out-of-stock items cannot be ordered.
- **Category Control:** Create, organize, and re-order menu categories.
- **Staff & Account Management:** Register kitchen operators and toggle account active/deactivated statuses.
- **Operational Settings:** Dynamically configure **Average Preparation Time** (mins) and food court branding.

---

## 🏗️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4, Html5Qrcode |
| **Backend** | Python 3.12+, Flask 3.1, Jinja2 Templates, Application Factory & Blueprints |
| **Database** | MySQL Server 8.0, Flask-SQLAlchemy 3.1, PyMySQL driver, Cryptography |
| **Security & Auth** | Flask Session, Werkzeug PBKDF2 Password Hashing, Flask-WTF CSRF Protection, Role-Based Access Control |
| **QR Engine** | Python `qrcode[pil]` with Pillow image rendering |
| **Configuration** | `python-dotenv` with `.env` environment variables |
| **Testing** | `pytest` test suite with in-memory SQLite isolation and live MySQL integration |

---

## 🗄️ Database Architecture (`smart_food_court`)

The system utilizes a 3NF normalized MySQL database schema:

```
users ───────────────< orders (user_id nullable for guest checkout)
categories ──────────< menu_items
orders ──────────────< order_items (preserves purchase item name & unit price)
orders ──────────────1 queue_entries (sequential daily queue tokens: Q-101, Q-102...)
orders ──────────────1 payment_records (Cash on Pickup / Demo UPI, status: Pending / Paid)
application_settings (key-value store for avg_prep_time, food_court_name)
```

---

## 📂 Project Structure

```
d:\newfoodcourt\
│
├── app/
│   ├── __init__.py               # Flask application factory, before_request user loader, error handlers
│   ├── extensions.py             # SQLAlchemy & CSRFProtect instances
│   ├── models.py                 # MySQL models: User, Category, MenuItem, Order, OrderItem, QueueEntry, PaymentRecord, ApplicationSetting
│   ├── auth/                     # Authentication blueprint (Login, Register, Logout, Role decorators)
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── utils.py
│   ├── student/                  # Student ordering blueprint (Home, Menu, Cart, Checkout, Confirmation, Tracker, API)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── staff/                    # Kitchen staff blueprint (Kitchen board, QR verification, handover)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── admin/                    # Admin portal blueprint (Dashboard, Chart.js analytics, Menu CRUD, Users, Settings)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/                 # Core business logic layer
│   │   ├── __init__.py
│   │   ├── order_service.py      # Cart validation, atomic MySQL order placement, server-side pricing
│   │   ├── queue_service.py      # Queue numbering, position estimation, lifecycle state transitions
│   │   └── qr_service.py         # Secure QR token creation, PNG image generation, QR payload parser
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Warm orange (#ff6b35) & deep green (#15803d) theme
│   │   ├── js/
│   │   │   └── main.js           # LocalStorage cart engine, live status polling, toasts
│   │   ├── images/               # Food placeholders and media
│   │   └── qr_codes/             # Generated order QR pass PNG files
│   └── templates/                # Jinja2 templates
│       ├── base.html             # Navigation bar, cart badge, alert messages, footer
│       ├── home.html             # Hero banner, featured dishes, live queue ticker
│       ├── menu.html             # Categorized menu, search bar, dietary filters, food cards
│       ├── cart.html             # Interactive shopping cart and price calculation
│       ├── checkout.html         # Contact details, payment method selection, order review
│       ├── order_confirmation.html# Order confirmation, token badge, QR code download
│       ├── track_order.html      # 5-step animated tracker, live queue spot, cancel modal
│       ├── queue_board.html      # Cafeteria live TV queue screen
│       ├── login.html            # Role login with quick-fill demo presets
│       ├── register.html         # Student registration form
│       ├── order_history.html    # Logged-in student past orders
│       ├── admin/
│       │   ├── dashboard.html    # Real-time metrics & Chart.js daily orders/sales charts
│       │   ├── menu.html         # Add/Edit modals, delete, stock toggle switch
│       │   ├── categories.html   # Category management
│       │   ├── orders.html       # Order ledger, search, status override
│       │   ├── users.html        # Staff accounts, student list, account activation
│       │   └── settings.html     # Operational parameters (avg prep time)
│       ├── staff/
│       │   ├── dashboard.html    # Kitchen display system with status chips & action buttons
│       │   └── verify.html       # Camera QR scanner, manual input, duplicate prevention
│       └── errors/
│           ├── 403.html          # Forbidden error
│           ├── 404.html          # Not found error
│           └── 500.html          # Internal server error
│
├── scripts/
│   ├── seed_data.py              # Idempotent seeder: 5 categories, 16 dishes, default accounts
│   ├── create_admin.py           # CLI utility to securely create administrator accounts
│   └── test_live_mysql.py        # End-to-end integration verification against local MySQL
│
├── tests/                        # Automated Pytest suite
│   ├── conftest.py               # Test app setup, in-memory DB isolation, sample fixtures
│   ├── test_models.py            # Password hashing, role checks, historical price snapshot
│   ├── test_auth.py              # Registration, login, unauthorized access 403 checks
│   ├── test_student_and_orders.py# Public menu browsing, stock validation, QR generation, cancel rules
│   └── test_queue_and_pickup.py  # State transitions, duplicate pickup protection, QR parsing
│
├── config.py                     # Development, Testing, and Production configuration classes
├── requirements.txt              # Production Python package requirements
├── .env.example                  # Environment template
├── .env                          # Local environment configuration
├── .gitignore                    # Git exclusions
├── run.py                        # Entry point with dev server & Flask CLI management commands
└── README.md                     # Comprehensive documentation
```

---

## 🚀 Setup and Run Instructions (Windows 11 & VS Code)

Follow these exact steps in Windows PowerShell.

### Step 1: Open Project in VS Code
1. Launch **Visual Studio Code**.
2. Open terminal in the project directory:
   ```powershell
   cd D:\newfoodcourt
   code .
   ```

### Step 2: Create and Activate Python Virtual Environment
In the VS Code PowerShell terminal:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an ExecutionPolicy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and re-run activate).*

### Step 3: Install Required Packages
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure MySQL Database
Make sure your MySQL 8.0 server service is running. Connect to MySQL with your admin user (e.g. `root`) and create the database and dedicated user:

```sql
-- Open MySQL Command Line Client or Workbench and run:
CREATE DATABASE IF NOT EXISTS smart_food_court CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'foodcourt_user'@'localhost' IDENTIFIED BY 'foodcourt_pass123';
GRANT ALL PRIVILEGES ON smart_food_court.* TO 'foodcourt_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 5: Configure Environment File (`.env`)
Ensure your `.env` file in `D:\newfoodcourt\.env` contains:
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=smartfoodcourt-secure-session-key-college-2026-prod-hash

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=foodcourt_user
MYSQL_PASSWORD=foodcourt_pass123
MYSQL_DB=smart_food_court

DATABASE_URL=mysql+pymysql://foodcourt_user:foodcourt_pass123@localhost:3306/smart_food_court
```

### Step 6: Initialize Database Tables
Run the Flask CLI initialization command:
```powershell
flask init-db
```
*Output: `Database tables created successfully in MySQL!`*

### Step 7: Populate Demo Food Items & Categories
Run the demo seeder:
```powershell
flask seed-db
```
*Output: `Demo food court data seeded successfully!`*

This populates 5 categories, 16 student cafeteria menu items with images, and the initial user accounts.

### Step 8: (Optional) Create Custom Administrator
To create a new custom administrator account:
```powershell
flask create-admin --username myadmin --email myadmin@campus.edu --password MySecurePass@123 --fullname "Chief Food Officer"
```
Or use the script directly:
```powershell
python scripts/create_admin.py --username admin2 --email admin2@foodcourt.edu --password Admin@123 --name "Operations Lead"
```

### Step 9: Start the Development Server
```powershell
python run.py
```
*Output:*
```
 * Serving Flask app 'run.py'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

### Step 10: Open in Browser & Test Workflows
Navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Pre-Seeded Default Accounts

For rapid grading, demonstration, and pair testing:

| Role | Username | Password | Direct Dashboard URL |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@123` | `http://127.0.0.1:5000/admin/dashboard` |
| **Kitchen Staff** | `staff` | `Staff@123` | `http://127.0.0.1:5000/staff/dashboard` |
| **Student** | `student` | `Student@123` | `http://127.0.0.1:5000/student/orders` |

*(The login page at `/auth/login` includes one-click preset buttons to auto-fill these credentials).*

---

## 🧪 Automated Testing Results

The project includes unit, integration, and security tests in `tests/`.

Run the test suite anytime:
```powershell
pytest -v
```

### Test Suite Execution Output:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\newfoodcourt
collected 17 items

tests/test_auth.py::test_student_registration PASSED                     [  5%]
tests/test_auth.py::test_student_registration_duplicate_username PASSED  [ 11%]
tests/test_auth.py::test_valid_login PASSED                              [ 17%]
tests/test_auth.py::test_invalid_login_rejected PASSED                   [ 23%]
tests/test_auth.py::test_unauthorized_admin_access_rejected PASSED       [ 29%]
tests/test_auth.py::test_unauthorized_staff_access_rejected PASSED       [ 35%]
tests/test_models.py::test_user_password_hashing PASSED                  [ 41%]
tests/test_models.py::test_user_roles PASSED                             [ 47%]
tests/test_models.py::test_historical_price_preservation PASSED          [ 52%]
tests/test_queue_and_pickup.py::test_order_lifecycle_and_duplicate_pickup_prevention PASSED [ 58%]
tests/test_queue_and_pickup.py::test_invalid_status_transition_rejected PASSED [ 64%]
tests/test_queue_and_pickup.py::test_qr_payload_parsing_and_token_match PASSED [ 70%]
tests/test_queue_and_pickup.py::test_unique_order_number_generation PASSED [ 76%]
tests/test_student_and_orders.py::test_public_menu_browsing PASSED       [ 82%]
tests/test_student_and_orders.py::test_valid_order_creation_and_pricing PASSED [ 88%]
tests/test_student_and_orders.py::test_out_of_stock_item_cannot_be_ordered PASSED [ 94%]
tests/test_student_and_orders.py::test_order_cancellation_updates_queue PASSED [100%]

====================== 17 passed in 13.03s ======================
```

### Live MySQL Integration Test:
```powershell
python scripts/test_live_mysql.py
```
*Output:*
```
[*] Initializing Flask app with development (MySQL) configuration...
[+] Real MySQL connection verified!
[+] Loaded 16 available menu items directly from MySQL.
[*] Placing live order through OrderService...
[+] Order #ORD-20261009-9906 created successfully in MySQL!
    - Total Amount: Rs. 200.00
    - Queue Token: Q-101
    - QR Image: qr_codes/ORD-20261009-9906.png
[+] QR code file verified at: D:\newfoodcourt\app\static\qr_codes\ORD-20261009-9906.png
[+] Active Queue Position: #1, Estimated Wait: ~8 mins
[*] Staff advances order: Pending -> Accepted...
[*] Staff advances order: Accepted -> Preparing...
[*] Staff advances order: Preparing -> Ready for Pickup...
[+] QR verification payload matched exactly.
[*] Staff verifies pickup and completes order...
[+] Order completed and Cash payment marked as PAID.
[*] Testing duplicate pickup attempt on completed order...
[+] Duplicate pickup prevented as expected! Message: 'Completed orders cannot be modified or collected again.'
[+] Admin Total Sales in MySQL: Rs. 200.00
=======================================================
ALL END-TO-END MYSQL INTEGRATION WORKFLOWS PASSED 100%!
=======================================================
```

---

## 🛠️ Common Troubleshooting

1. **MySQL Connection Error (`Access denied for user` or `Can't connect to MySQL server`)**:
   - Verify that your MySQL server service is running (`Get-Service MySQL*` in PowerShell).
   - Verify credentials in `.env` match your MySQL credentials (`foodcourt_user` / `foodcourt_pass123` or `root`).
2. **Port 5000 Already In Use**:
   - Change the port in PowerShell:
     `$env:PORT="5050"; python run.py`
     and open `http://127.0.0.1:5050`.
3. **Camera QR Scanner Permission Denied**:
   - Modern browsers require HTTPS or `localhost`/`127.0.0.1` to grant camera permissions. Use the fallback manual order number input on the verification page if camera access is restricted.

---

## 📜 License
Developed for Academic & Food Court Operations. Free to customize, extend, and deploy.
