import sys
import traceback
from flask import Flask

try:
    print("Initializing Flask app...")
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return {'message': 'Hello World'}

    if __name__ == '__main__':
        print("Starting Flask server...")
        app.run(debug=True, host='127.0.0.1', port=5000)
except Exception as e:
    print(f"Error: {str(e)}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)