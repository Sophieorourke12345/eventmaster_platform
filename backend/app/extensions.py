from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()
login_manager = LoginManager()
migrate = Migrate()

