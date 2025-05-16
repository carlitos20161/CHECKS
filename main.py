from app import app
from routes import configure_routes
import logging
logging.basicConfig(level=logging.DEBUG)


# Configure all the routes
configure_routes(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, debug=True)
