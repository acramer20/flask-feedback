from email import message
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm, DeleteForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
db.create_all()

@app.route('/')
def to_register():
    """redirects user to register form"""
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """allows user to register with app"""
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        db.session.commit()
        # try: 
        #     db.session.commit()
        # except IntegrityError:
        #     form.username.errors.append('Username taken. Please pick another.')
        #     return render_template('register.html', form=form)
        session['user_id'] = new_user.id
        flash('Welcome! Successfully created your account!', 'success')
        return redirect(f'/users/{new_user.id}')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form= LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user: 
            flash(f"Welcome Back, {user.username}!", 'primary')
            session['user_id']=user.id
            return redirect(f'/users/{user.id}')
        else: 
            form.username.errors=['Invalid username/password.']
    return render_template('login.html', form=form)

@app.route('/users/<int:id>')
def user_page(id):
    """only logged in users should be able to see the secret page"""
    if 'user_id' not in session:
        flash('Please login first', 'danger')
        return redirect('/')
    user = User.query.get(id)
    form = DeleteForm()
    return render_template('user.html', user=user, form=form)

@app.route("/users/<int:id>/delete", methods=["POST"])
def remove_user(id):
    """Remove user nad redirect to login."""

    if "user_id" not in session:
        return redirect('/')

    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    session.pop("user_id")

    return redirect("/login")

@app.route('/logout')
def logout_user():
    """logs user out but better to use post request apparently"""
    session.pop('user_id')
    flash('Successfully logged out!', 'primary')
    return redirect('/')

@app.route('/users/<int:id>/delete')
def delete_user(id):
    """deleting user and going to the login page"""
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get_or_404(id)
    db.session.delete(id)
    db.session.commit()
    session.pop('user_id')

    return redirect('/login')


@app.route("/users/<int:id>/feedback/add", methods=["GET", "POST"])
def add_feedback(id):
    """show the add feedback form"""

    if 'user_id' not in session:
        return redirect('/')

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(
            title=title,
            content=content,
            user_id=id,
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(f"/users/{feedback.user_id}")

    else:
        return render_template("feedback/add.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""

    feedback = Feedback.query.get(feedback_id)

    if "user_id" not in session:
        return redirect('/')

    form = FeedbackForm(obj=feedback)
    # don't really understand why we need obj=feedback ***************

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.user_id}")

    return render_template("/feedback/edit.html", form=form, feedback=feedback)


@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "user_id" not in session:
        return redirect('/')

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.user_id}")