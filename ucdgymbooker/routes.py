from flask import render_template, redirect, url_for, flash
from ucdgymbooker import app
from ucdgymbooker.models import User, Timeslot, Reservation
#from flask_wtf import wtforms
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length
from functools import wraps
from ucdgymbooker.helpers import timezone_converter

from ucdgymbooker import db, bcrypt
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#Used to reload user id from user object that is stored in the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    #
    username = IntegerField('name', validators=[InputRequired()], description="Your UCD student number", render_kw={"placeholder":"Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=7, max=80)], description="You can use any password", render_kw={"placeholder":"Password"})
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = IntegerField('name', validators=[InputRequired()],
                            description="Your UCD student number", render_kw={"placeholder": "Username"})
    password = PasswordField('password', validators=[InputRequired(), Length(min=7, max=80)],
                             description="You can use any password", render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

    #password = StringField('name', validators=[InputRequired()])



#setup routes, the decorator matches a route to a function, the default directory name for templates is "templates" so you only need to specify the filename
@app.route('/')
def index():
    return render_template("index.html")




@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('timeslots'))
    return render_template("login.html", form=form)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pwd, verified=False, admin=False)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


#TODO double check all reservation and modification requests with current user variable
#https://stackoverflow.com/questions/44697201/prevent-user-to-edit-other-users-profile
#TODO convert back to dublin time
#TODO order poolside and performance using append and prepend
@app.route('/timeslots')
@login_required
def timeslots():
    data = Timeslot.query.filter(Timeslot.time >= timezone_converter.get_current_utc_timestamp())

    info = {"dates":[]}
    #if "keyword" in info
    for elem in data:
        time = timezone_converter.utc_to_ie(elem.time)
        gym = elem.gym
        id = elem.id

        #%A %B for fullnames
        date_string = time.strftime("%a %d %b %Y")
        time_string = time.strftime("%H:%M")

        if not date_string in info:
            info["dates"].append(date_string)
            info[date_string] = {}
            info[date_string]["hours"] = []
        if not time_string in info[date_string]:
            info[date_string][time_string] = []
            info[date_string]["hours"].append(time_string)
        list = [id, gym]
        print(gym)
        if gym == "Poolside Gym":
            info[date_string][time_string].append(list)
        else:
            info[date_string][time_string].insert(0, list)







        #print(elem)
    #data structure => dict with date which has more dicts with hours as key and
    print(info["dates"])
    print(info[info["dates"][1]])
    #date string, hour, minute, gym, id

    return render_template("timeslots.html", data=info)

@app.route('/reservations')
@login_required
def reservations():
    data = Reservation.query.filter_by(user_id=current_user.get_id())


    return render_template("reservations.html", data=data)

@app.route('/reserve/<int:reservation_id_1>', methods = ['POST'])
@app.route('/reserve/<int:reservation_id_1>/<int:reservation_id_2>', methods = ['POST'])
@login_required
def reserve(reservation_id_1, reservation_id_2=0):
    #if request.method == 'GET':

    new_reservation_1 = Reservation(status='Booked', user_id=current_user.get_id(), timeslot_id=reservation_id_1, priority=1)
    db.session.add(new_reservation_1)
    db.session.commit()

    if not reservation_id_2 == 0:
        new_reservation_2 = Reservation(status='Booked', user_id=current_user.get_id(), timeslot_id=reservation_id_2,
                                        priority=2)
        db.session.add(new_reservation_2)
        db.session.commit()


    return redirect('/reservations', code=302)

@app.route('/cancel/<int:reservation_id>', methods = ['POST'])
@login_required
def cancel(reservation_id):
    #if request.method == 'GET':
    data = Reservation.query.filter_by(user_id = current_user.get_id())
    if not reservation_id == 0:
        print("lala")


    return render_template("reservations.html", data=data)


#Modified from https://stackoverflow.com/questions/61939800/role-based-authorization-in-flask-login
#A more conventional way would be to use flask-user instead of flask-login with extra decorators but there is only one additional role
def admin_required(func):
    """
    Modified login_required decorator to restrict access to admin group.
    """

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            flash('You do not have permission to access this resource.', 'warning')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_view

@app.route('/statistics')
@login_required
@admin_required
def statistics():

    data = Timeslot.query.all()

    return render_template("timeslots.html", data=data)

@app.route('/admin_panel')
@login_required
@admin_required
def admin_panel():

    data = Timeslot.query.all()

    return render_template("timeslots.html", data=data)