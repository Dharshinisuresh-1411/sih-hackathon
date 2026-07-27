from flask import Flask, render_template
from flask_cors import CORS
from sqlalchemy import inspect, text
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    with app.app_context():
        inspector = inspect(db.engine)
        if inspector.has_table("complaints"):
            existing_columns = {column["name"] for column in inspector.get_columns("complaints")}
            if "remarks" not in existing_columns:
                db.session.execute(text("ALTER TABLE complaints ADD COLUMN remarks TEXT"))
                db.session.commit()

    from routes.pole_routes import pole_bp
    from routes.complaint_routes import complaint_bp
    from routes.electrician_routes import electrician_bp
    from routes.report_routes import report_bp

    app.register_blueprint(pole_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(electrician_bp)
    app.register_blueprint(report_bp)

    # ---- Page routes (server-rendered shell, JS fetches data from the API) ----
    @app.route("/")
    def dashboard():
        return render_template("dashboard.html", active="dashboard")

    @app.route("/poles")
    def poles_page():
        return render_template("poles.html", active="poles")

    @app.route("/complaints/new")
    def complaint_form_page():
        return render_template("complaint_form.html", active="new_complaint")

    @app.route("/complaints")
    def complaints_page():
        return render_template("complaints.html", active="complaints")

    @app.route("/complaints/open")
    def open_complaints_page():
        return render_template("open_complaints.html", active="open")

    @app.route("/electricians")
    def electricians_page():
        return render_template("electricians.html", active="electricians")

    @app.route("/assign")
    def assign_page():
        return render_template("assign.html", active="assign")

    @app.route("/repeat-offenders")
    def repeat_offenders_page():
        return render_template("repeat_offenders.html", active="repeat")

    # ---- Graceful error handlers (FAILURE CASE 3) ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("dashboard.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("Server error: %s", e)
        return {"error": "Unable to process your request because the database is "
                          "temporarily unavailable. Please try again."}, 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
