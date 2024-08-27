"""
This module contains the Flask app that serves the API endpoints for the normalizeHours function.

The app has the following routes:
- GET /: Returns a simple message to confirm that the app is running.
- GET /normalizeHours/<inputString>: Returns the normalized hours from the input string.

The app also has error handlers for the following status codes:
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

The app is run with the following command:
```
python app.py
```

The app can be accessed at http://localhost:5000

The app requires the following packages:
* Flask
* flask_cors
"""

# IMPORTS
from flask import Flask, jsonify, abort
from flask_cors import CORS
from normalizeHours import normalize_input_string


# Create a new Flask app
app = Flask(__name__)
CORS(app)


# ERROR HANDLERS
@app.errorhandler(400)
def bad_request(
    e: Exception,
) -> tuple:
    """
    """
    return {"Error": str(e)}, 400

@app.errorhandler(404)
def not_found(
    e: Exception,
) -> tuple:
    """
    """
    return {"Error": str(e)}, 404

@app.errorhandler(500)
def internal_server_error(
    e: Exception,
) -> tuple:
    """
    """
    return {"Error": str(e)}, 500


# ROUTES
@app.route("/", methods=["GET"])
def root(
) -> tuple:
    """
    """
    return jsonify({"message": "Hello, World!"}), 200

@app.route("/normalizeHours/<inputString>", methods=["GET"])
def normalize_hours(
    inputString: str,
) -> tuple:
    """
    """
    try:
        response = normalize_input_string(inputString)
    except Exception as e:
        abort(400, description=str(e))
    return jsonify(response), 200


# MAIN
if __name__ == "__main__":
    app.run(debug=True, threaded=True)
