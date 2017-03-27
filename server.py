# This example is based closely on these examples:
# https://developers.google.com/api-client-library/python/auth/web-app
# https://developers.google.com/identity/sign-in/web/backend-auth

# Portions of this page are modifications based on work created and
# shared by Google and used according to terms described in the
# Creative Commons 3.0 Attribution License.
# (https://developers.google.com/terms/site-policies)
# (https://creativecommons.org/licenses/by/3.0/)

# Additionally, the Flask-Login portions are based on the example in the README
# of the Flask-Login project here:
# https://github.com/maxcountryman/flask-login
import json
import os

import datetime

import sheets

import flask

from oauth2client import client, crypt

import flask_login

app = flask.Flask(__name__)

EMAIL_SCOPE = "https://www.googleapis.com/auth/userinfo.email"

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Populated from file specified as environment variable, see main function
CLIENT_CONFIG = {}

# Mock database for now
# TODO: have real database
users = {}

SHEETS_SERVICE = None


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    user.data = users[email]
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        rendered = flask.render_template("index.html", client_id=CLIENT_CONFIG['web']['client_id'])
        return rendered

    token = flask.request.form['idtoken']
    client_id = CLIENT_CONFIG['web']['client_id']

    id_info = user_info_from_token(token, client_id)

    if id_info:
        user = User()
        user.id = id_info['email']

        if id_info['email'] not in users:
            users[id_info['email']] = id_info
        flask_login.login_user(user)

        return flask.redirect(flask.url_for('protected'))

    return 'Bad login'


def log_user_activity(email):
    ss_id = sheets.get_or_create_ss(SHEETS_SERVICE, "User Log")

    time_str = datetime.datetime.now().strftime('%m/%d/%Y %H:%M')
    data = [[email, time_str]]
    sheets.append_cells(SHEETS_SERVICE, ss_id, data)
    sheets.share_file(SHEETS_SERVICE, ss_id, email)

    return ss_id

@app.route('/')
@flask_login.login_required
def protected():
    ss_id = log_user_activity(flask_login.current_user.id)

    link = sheets.get_link(ss_id)

    return flask.render_template("protected.html", sheet_link=link, user_id=flask_login.current_user.id)

@login_manager.unauthorized_handler
def unauthorized_handler():
    return flask.redirect(flask.url_for('login'))


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'


def user_info_from_token(token, client_id):
    """Makes a call to Google's servers to exchange the token and client_id for the
    info corresponding to the token."""
    try:
        idinfo = client.verify_id_token(token, client_id)

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise crypt.AppIdentityError("Wrong issuer.")
    except crypt.AppIdentityError:
        # Invalid token
        return None
    return idinfo


def get_env_variable(var_name, description):
    if var_name not in os.environ:
        print ("Please specify %s as " +
               "the environment variable:\n%s") % (description, var_name)
        return None

    return os.environ[var_name]


def main():
    # Load the client secrets from the file downloaded from the
    # google cloud console
    client_secrets_path = get_env_variable('CLIENT_SECRETS_PATH', 'the path to the client secrets file')
    robot_creds_path = get_env_variable('ROBOT_CREDS_PATH', 'the path to robot account credentials file')

    if client_secrets_path is None or robot_creds_path is None:
        return

    with open(client_secrets_path, "r") as fh:
        global CLIENT_CONFIG
        CLIENT_CONFIG = json.load(fh)

    global SHEETS_SERVICE
    SHEETS_SERVICE = sheets.get_sheets_service(robot_creds_path)

    # Secret key required for sessions
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()


if __name__ == '__main__':
    main()