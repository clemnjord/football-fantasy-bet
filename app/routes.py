import http.client
import json

from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Match, Team
from datetime import datetime
from app.football_api_helper import FootballDataApi
from sqlalchemy.orm import joinedload


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template("index.html", title='Home Page')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/matchs')
def matches():
    connection = http.client.HTTPConnection('api.football-data.org')
    headers = { 'X-Auth-Token': 'fe4c5aaa344a40a78cef8547f5840478' }
    connection.request('GET', '/v2/competitions/2015/matches?dateFrom=2019-01-01&dateTo=2019-01-31', None, headers )
    response = json.loads(connection.getresponse().read().decode())
    connection.close()

    if "matches" not in response:
        return "no matches\n"

    for match_api in response['matches']:
        home_team = Team.query.filter(Team.name == match_api["homeTeam"]["name"]).first()
        if home_team is None:
                home_team = Team()
                home_team.name = match_api["homeTeam"]["name"]
                db.session.add(home_team)
                db.session.commit()

        away_team = Team.query.filter(Team.name == match_api["awayTeam"]["name"]).first()
        if away_team is None:
                away_team = Team()
                away_team.name = match_api["awayTeam"]["name"]
                db.session.add(away_team)
                db.session.commit()

        match = Match.query.options(joinedload(Match.home_team), joinedload(Match.away_team)).filter(Match.home_team_id == home_team.id and Match.away_team_id == away_team.id).first()

        # The match does not exist. We must add it to the database
        #if match is None:
        #    match = Match()
        #    match.date = match_api["utcDate"]
        #    match.date = match_api["status"]

            #match.set
    return "no error ?\n" + str(response)