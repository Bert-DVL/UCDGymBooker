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
    name = StringField('fullname', validators=[InputRequired()], description="Your full name", render_kw={"placeholder":"Full Name"})
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
                return redirect(url_for('timeslots'), code=302)
    return render_template("login.html", form=form)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_pwd = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_pwd, name=form.name.data, verified=False, admin=False)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'), code=302)
    return render_template("register.html", form=form)

@app.route('/logout', methods = ['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'), code=302)


#TODO double check all reservation and modification requests with current user variable
#https://stackoverflow.com/questions/44697201/prevent-user-to-edit-other-users-profile
#TODO convert back to dublin time
#TODO order poolside and performance using append and prepend
#TODO separate days into different requests if issues arise with performance
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


        date_string = timezone_converter.get_date_string(time)
        time_string = timezone_converter.get_time_string(time)

        if not date_string in info:
            info["dates"].append(date_string)
            info[date_string] = {}
            info[date_string]["hours"] = []
        if not time_string in info[date_string]:
            info[date_string][time_string] = []
            info[date_string]["hours"].append(time_string)
        info_list = [id, gym]
        print(gym)
        if gym == "Poolside Gym":
            info[date_string][time_string].append(info_list)
        else:
            info[date_string][time_string].insert(0, info_list)







    #print(elem)
    #data structure => dict with date which has more dicts with hours as key and
    #print(info["dates"])
    #print(info[info["dates"][1]])
    #date string, hour, minute, gym, id

    return render_template("timeslots.html", data=info)

#TODO only take reservations past current date
@app.route('/reservations')
@login_required
def reservations():
    #data = Reservation.query.filter_by(user_id=current_user.get_id()).join(Timeslot)
    data = db.session.query(Reservation, Timeslot).join(Timeslot).filter(Reservation.user_id==current_user.get_id())
    print(data)



    info = []

    for reservation, timeslot in data:
        info_elem = {}

        time = timezone_converter.utc_to_ie(timeslot.time)
        date_string = timezone_converter.get_date_string(time) + ', ' + timezone_converter.get_time_string(time)
        info_elem['date'] = date_string

        gym = timeslot.gym
        info_elem['gym'] = gym

        id = reservation.id
        info_elem['id'] = id

        status = reservation.status
        info_elem['status'] = status

        priority = 'Primary'
        if reservation.priority == 2:
            priority = 'Secondary'

        info_elem['priority'] = priority

        info.append(info_elem)




    return render_template("reservations.html", data=info)

@app.route('/reserve/<int:reservation_id_1>', methods = ['POST'])
@app.route('/reserve/<int:reservation_id_1>/<int:reservation_id_2>', methods = ['POST'])
@login_required
def reserve(reservation_id_1, reservation_id_2=0):
    #if request.method == 'GET':

    now = timezone_converter.get_current_utc_timestamp()

    priority_num = 0

    if not reservation_id_2 == 0:
        priority_num = 1



    new_reservation_1 = Reservation(status='Booked', user_id=current_user.get_id(), timeslot_id=reservation_id_1,
                                    priority=priority_num, reservation_time=now)
    db.session.add(new_reservation_1)
    db.session.commit()



    if not reservation_id_2 == 0:

        new_reservation_2 = Reservation(status='Booked', user_id=current_user.get_id(), timeslot_id=reservation_id_2,
                                        priority=2, reservation_time=now)
        db.session.add(new_reservation_2)
        db.session.commit()


    return redirect('/reservations', code=302)

@app.route('/delete_confirm/<int:reservation_id>', methods = ['POST'])
@login_required
def delete_confirm(reservation_id):
    data = db.session.query(Reservation, Timeslot).join(Timeslot).filter(Reservation.id == reservation_id).one()
    print(data)

    info = {}

    time = timezone_converter.utc_to_ie(data[1].time)
    date_string = timezone_converter.get_date_string(time) + ', ' + timezone_converter.get_time_string(time)
    info['date'] = date_string

    gym = data[1].gym
    info['gym'] = gym

    id = data[0].id
    info['id'] = id

    return render_template("delete_confirm.html", data=info)


@app.route('/delete/<int:reservation_id>', methods = ['POST'])
@login_required
def delete(reservation_id):
    #if request.method == 'GET':

    reservation = db.session.query(Reservation).filter(Reservation.id == reservation_id, Reservation.user_id==current_user.get_id()).first()
    db.session.delete(reservation)
    db.session.commit()

    return redirect(url_for('reservations'), code=302)


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

@app.route('/database')
@login_required
@admin_required
def database():

    data = Timeslot.query.all()

    return render_template("database.html", data=data)

@app.route('/admin_panel')
@login_required
@admin_required
def admin_panel():

    data = User.query.all()

    return render_template("admin_panel.html", data=data)

@app.route('/modify_user/<int:user_id>/<string:action>', methods = ['POST'])
@login_required
@admin_required
def modify_user(user_id, action):
    user = User.query.filter(User.id == user_id).first()


    if action == 'confirm':
        user.verified = True
    if action == 'disconfirm':
        user.verified = False
    if action == 'add_admin':
        user.admin = True
    if action == 'remove_admin':
        if current_user.get_id() > user.id:
            flash('You cannot remove admin privileges from a user who registered before you.')
        else:
            user.admin = False
    if action == 'delete':
        if user.admin:
            flash('You cannot remove a user if they are an admin, remove their admin status before deleting.')
        else:
            db.session.delete(user)
    db.session.commit()





    data = User.query.all()

    return redirect(url_for('admin_panel'), code=302)