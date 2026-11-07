import os
import secrets

from flask import Flask, abort, flash, redirect, session, request, url_for

from . import db
from .messages import MSG


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-apenas-para-testes"),
        DB_ENGINE=os.environ.get("DB_ENGINE", "mysql"),
        DB_HOST=os.environ.get("DB_HOST", "127.0.0.1"),
        DB_PORT=int(os.environ.get("DB_PORT", "3306")),
        DB_NAME=os.environ.get("DB_NAME", "labagenda"),
        DB_USER=os.environ.get("DB_USER", "labagenda_app").strip(),
        DB_PASSWORD=os.environ.get("DB_PASSWORD", "").strip(),
        DB_SSL_CA=os.environ.get("DB_SSL_CA", ""),      # caminho do certificado CA (opcional)
        SQLITE_PATH=os.environ.get("SQLITE_PATH", "labagenda_dev.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "0") == "1",  # ligar em produção (HTTPS)
        VERSAO="2.2.1",
    )
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(db.close_conn)

    @app.before_request
    def proteger_csrf():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        if request.method == "POST":
            token = request.form.get("csrf", "")
            if not secrets.compare_digest(token, session["csrf"]):
                flash(MSG["E23"], "erro")
                return redirect(request.referrer or url_for("main.login"))

    @app.context_processor
    def injetar():
        return {"versao": app.config["VERSAO"], "csrf_token": session.get("csrf", ""),
                "usuario_atual": {"nome": session.get("nome"), "perfil": session.get("perfil")}
                if "uid" in session else None}

    from .routes import bp
    app.register_blueprint(bp)
    return app
