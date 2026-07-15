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
    try:
        db.create_all()
    except Exception as e:
        print(f"[Startup] Warning: db.create_all failed: {e}")


import os
import threading
import time

app.register_blueprint(employee_bp)

@app.route("/init-db")
@app.route("/init_db")
def init_db_root():
    import traceback
    try:
        print("[DB Init] Recreating all database tables...")
        try:
            # Disable foreign key checks for MySQL during drop/create
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
            db.session.commit()
        except Exception as e:
            print(f"[DB Init] Non-MySQL database or error setting FK checks: {e}")
            
        db.drop_all()
        db.create_all()
        
        try:
            # Re-enable foreign key checks
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
            db.session.commit()
        except Exception as e:
            pass
            
        print("[DB Init] Recreated successfully!")
        return "Database initialized successfully! Go back to <a href='/'>Dashboard</a>."
    except Exception as e:
        return f"<pre>Error Recreating Database:\n{traceback.format_exc()}</pre>", 500

@app.route("/test-db")
@app.route("/test_db")
def test_db_pymysql():
    import pymysql
    import os
    import traceback
    
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT')
    if port and ':' not in host:
        host = f"{host}:{port}"
        
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    html = f"""
    <h3>Direct PyMySQL Connection Diagnostic</h3>
    <p><strong>DB_HOST:</strong> {host}</p>
    <p><strong>DB_USER:</strong> {user}</p>
    <p><strong>DB_NAME:</strong> {db_name}</p>
    <p><strong>DB_PASSWORD configured:</strong> {'YES (Length: ' + str(len(password)) + ')' if password else 'NO'}</p>
    """
    
    try:
        ssl_args = None
        if 'localhost' not in host and '127.0.0.1' not in host:
            ssl_args = {"ssl_mode": "REQUIRED"}
            
        host_only = host
        port_num = 3306
        if ':' in host:
            parts = host.split(':')
            host_only = parts[0]
            port_num = int(parts[1])
            
        conn = pymysql.connect(
            host=host_only,
            port=port_num,
            user=user,
            password=password,
            database=db_name,
            ssl=ssl_args,
            connect_timeout=4
        )
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        conn.close()
        html += f"<p style='color:green;'><strong>SUCCESS!</strong> MySQL Version: {version[0]}</p>"
    except Exception as e:
        html += f"<p style='color:red;'><strong>FAILED!</strong> Connection Traceback:</p><pre>{traceback.format_exc()}</pre>"
        
    return html





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

