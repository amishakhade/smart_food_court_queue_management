"""
Authentication and authorization tests.
"""
from app.models import User, UserRole


def test_student_registration(client, app):
    """Test successful student self-registration."""
    resp = client.post('/auth/register', data={
        'full_name': 'Neha Patel',
        'username': 'neha_patel',
        'email': 'neha@campus.edu',
        'phone': '9811223344',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        u = User.query.filter_by(username='neha_patel').first()
        assert u is not None
        assert u.role == UserRole.STUDENT
        assert u.check_password('Password123') is True


def test_student_registration_duplicate_username(client):
    """Test duplicate registration is cleanly rejected."""
    resp = client.post('/auth/register', data={
        'full_name': 'Duplicate User',
        'username': 'student',  # already seeded in conftest
        'email': 'different@campus.edu',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Username is already taken" in resp.data


def test_valid_login(client):
    """Test valid login creates session."""
    resp = client.post('/auth/login', data={
        'identifier': 'student',
        'password': 'Student@123'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Aarav Student" in resp.data or b"Sign Out" in resp.data


def test_invalid_login_rejected(client):
    """Test wrong password login rejection."""
    resp = client.post('/auth/login', data={
        'identifier': 'student',
        'password': 'WrongPassword999'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Invalid credentials" in resp.data


def test_unauthorized_admin_access_rejected(client):
    """Ensure non-admin user cannot access admin dashboard."""
    # 1. Unauthenticated request
    resp = client.get('/admin/dashboard')
    assert resp.status_code == 302  # redirects to login

    # 2. Log in as student
    client.post('/auth/login', data={'identifier': 'student', 'password': 'Student@123'})
    resp_student = client.get('/admin/dashboard')
    assert resp_student.status_code == 403  # Forbidden for students


def test_unauthorized_staff_access_rejected(client):
    """Ensure student cannot access kitchen staff dashboard."""
    client.post('/auth/login', data={'identifier': 'student', 'password': 'Student@123'})
    resp = client.get('/staff/dashboard')
    assert resp.status_code == 403
