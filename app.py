import sys
import io

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass


from flask import Flask
from config import Config
from extensions import db

from routes.employee_routes import employee_bp
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

from models.employee import Employee

with app.app_context():
    db.create_all()

import os
import threading
import time

app.register_blueprint(employee_bp)

@app.route("/init-db")
@app.route("/init_db")
def init_db_root():
    print("[DB Init] Recreating all database tables...")
    db.drop_all()
    db.create_all()
    print("[DB Init] Recreated successfully!")
    return "Database initialized successfully! Go back to <a href='/'>Dashboard</a>."


def start_email_poller():
    # Only start the thread in the main reloader process in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        def poll_loop():
            time.sleep(5)  # Wait for server startup
            print("[Background Poller] Starting background thread...")
            while True:
                try:
                    with app.app_context():
                        from process_inbox import poll_and_process_emails
                        poll_and_process_emails()
                except Exception as e:
                    print(f"[Background Poller] Error: {e}")
                time.sleep(60)
        
        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()

if not os.environ.get('VERCEL'):
    start_email_poller()

if __name__ == "__main__":
    app.run(debug=True)

