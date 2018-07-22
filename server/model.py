from server.app import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu = db.Column(db.TEXT)
