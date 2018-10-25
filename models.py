from app import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.column(db.Text)