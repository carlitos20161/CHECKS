import pytest
from app import app as flask_app, db as _db
from models import User, Check, Company, CompanyClient, Bank, Employee
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test"
    })

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_user(app):
    with app.app_context():
        user = User(username="testuser", password_hash=generate_password_hash("1234"), role="user")
        _db.session.add(user)
        _db.session.commit()
        return user

def login(client, username="testuser", password="1234"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

def test_check_creation(client, app, init_user):
    with app.app_context():
        # Create required objects
        bank = Bank(name="CHASE", routing_number="111000", account_number="12345678")
        _db.session.add(bank)
        _db.session.commit()

        company = Company(
            name="TestCo",
            address="123 Main St",
            logo="test_logo.png",
            default_bank_id=bank.id
        )

        client_obj = CompanyClient(
            name="Client A",
            address="456 Elm St",
            contact_person="Jane Smith",
            contact_email="jane@client.com",
            contact_phone="123-456-7890",
            company=company
        )

        employee = Employee(
            name="John Doe",
            title="Laborer",
            company=company,
            client=client_obj
        )

        _db.session.add_all([company, client_obj, employee])
        _db.session.commit()

        # Extract IDs for form submission
        company_id = company.id
        client_id = client_obj.id
        employee_id = employee.id

    login(client)

    # Submit check creation form
    response = client.post("/checks/create", data={
        "amount": "123.45",
        "date": "2025-06-18",
        "company_id": str(company_id),
        "client_id": str(client_id),
        "employee_id": str(employee_id)
    }, follow_redirects=True)

    assert b"created successfully" in response.data
