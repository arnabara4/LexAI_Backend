from flask import Flask
from .config import config
from .extensions import db, bcrypt, jwt, migrate, mail
from flask_cors import CORS
from app.auth import auth_bp
from app.RAG import RAG_bp

def create_app(config_name="default"):
    
    app = Flask(__name__)
    
    app.config.from_object(config[config_name])

    CORS(
        app,
        supports_credentials=True,
        origins=[app.config.get('FRONTEND_URL')]
    )

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload):
        from app.auth.models import RefreshToken

        jti = jwt_payload["jti"]

        if jwt_payload["type"] == "access":
            return False

        token_in_db = RefreshToken.query.filter_by(jti=jti).first()
        is_revoked = token_in_db is None
        return is_revoked

    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(RAG_bp)

    return app