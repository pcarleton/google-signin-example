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


@app.route('/')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id

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


def main():
    # Load the client secrets from the file downloaded from the
    # google cloud console
    env_var_name = 'CLIENT_SECRETS_PATH'
    if env_var_name not in os.environ:
        print ("Please specify the path to your client secrets file as " +
               "the environment variable:\n%s" % env_var_name)
        return

    client_secrets_path = os.environ[env_var_name]

    with open(client_secrets_path, "r") as fh:
        global CLIENT_CONFIG
        CLIENT_CONFIG = json.load(fh)

    # Secret key required for sessions
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()


if __name__ == '__main__':
    main()