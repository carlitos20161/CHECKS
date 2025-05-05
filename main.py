from app import app
from routes import configure_routes

# Configure all the routes
configure_routes(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
