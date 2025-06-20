import pytest
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_successful_login(client):
    user = User(username='tester', role='user')
    user.set_password('1234')
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'tester',
        'password': '1234'
    }, follow_redirects=True)

    assert b'Logged in successfully' in response.data
