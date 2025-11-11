from dotenv import load_dotenv
import os

load_dotenv()

from app import create_app

config_name = os.getenv('FLASK_CONFIG') or "default"
app = create_app(config_name)

if __name__ == "__main__":
    app.run(debug = True)