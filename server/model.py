from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu = db.Column(db.TEXT)
