from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.auth.forms import LoginForm, RegistrationForm
from app.models.user import User
from app import db
from app.auth import bp
from app.models.user import Role

@bp.route('/login', methods=['GET', 'POST'])
def login():
    current_app.logger.info('Accessing login page')
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
       form = RegistrationForm()
       if form.validate_on_submit():
           role_value = form.role.data.upper()  # Ensure the role is in uppercase
           if role_value not in [role.value for role in Role]:
               flash('Invalid role selected.', 'danger')
               return redirect(url_for('auth.register'))

           user = User(username=form.username.data, email=form.email.data, role=Role(role_value))
           user.set_password(form.password.data)
           db.session.add(user)
           db.session.commit()
           flash('Registration successful!', 'success')
           return redirect(url_for('auth.login'))
       return render_template('register.html', form=form)

@bp.route('/parser')
def parser():
    return render_template('main/parser.html')
