#from flask.ext.login import UserMixin  , UserMixin
from ucdgymbooker import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    #TODO string lengths
    username = db.Column(db.Integer, unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    verified = db.Column(db.Boolean, nullable=False)
    admin = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    #relationship to Reservation model, backref is like adding column to Reservation, if you query user_ids of a Reservation it will return said id, lazy is related to data loading
    #the relationship.backref keyword is only a common shortcut for placing a second relationship()
    #backref allows you to access the user that created sth directly instead of querying by id
    reservations = db.relationship('Reservation', backref='user', cascade="all, delete, delete-orphan", lazy=True)

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    #TODO change method in production
    def is_admin(self):
        return True

    def __repr__(self):
        return f"User (id: {self.id}, name:{self.name}, s_id:{self.username}, pwd: {self.password}, verified: {self.verified}, admin: {self.admin})"

#default = datetime.utcnow, not datetime.utcnow() => no parentheses as it would return a value that was evaluated when you start running the app instead of a returning function that gets evaluated at runtime
class Timeslot(db.Model):
    __tablename__ = 'timeslot'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime, nullable=False)
    reservations = db.relationship('Reservation', backref='timeslot', cascade="all, delete, delete-orphan", lazy=True)
    gym = db.Column(db.String(80), nullable=False)
    #backup_reservations = db.relationship('Reservation', backref='backup_timeslot_ids', lazy=True)

    def __repr__(self):
        return f"Timeslot (id: {self.id}, time: {self.time}, gym: {self.gym})"


#reservation is tied to both a timeslot and a gym, if you want to try one gym before another, 2 reservations get made where one has a higher priority number than the other
class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(80), nullable=False)
    #id of user who created reservation
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timeslot_id = db.Column(db.Integer, db.ForeignKey('timeslot.id'), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    reservation_time = db.Column(db.DateTime, nullable=False)
    #backup_timeslot_id = db.Column(db.Integer, db.ForeignKey('backup_timeslot.id'), nullable=True)
    def __repr__(self):
        return f"Reservation (id: {self.id}, status: {self.status}, uid: {self.user_id}, tid: {self.timeslot_id}, prio: {self.priority}, time: {self.reservation_time})"


