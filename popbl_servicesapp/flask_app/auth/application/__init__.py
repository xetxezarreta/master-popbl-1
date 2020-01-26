from flask import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from .config import Config
from .BLConsul import BLConsul

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine)
)

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False)
    with app.app_context():
        from . import routes
        from . import models
        from .auth_logic import AuthLogic
        models.Base.metadata.create_all(engine)
        auth_logic = AuthLogic()
        auth_logic.generate_keys()
        auth_logic.init_permissions()
        bl_consul = BLConsul.get_instance()
        bl_consul.init_and_register(app)
        return app
