# Google Login Example with Flask

This project is a simple example of using the Google login libraries with [Flask][1] and [Flask-Login][2].

It requires a user to log in and then shares a Google Sheet with them that logs their email address.

See the accompanying blog post [here][3]

## Runing the App

To run the app, set environment variables and then run server.py:

```
export CLIENT_SECRETS_PATH=  # Path to client credentials JSON file
export ROBOT_CREDS_PATH=  # Path to service account credentials JSON file
python server.py
```


[1]:http://flask.pocoo.org/
[2]:https://flask-login.readthedocs.io/en/latest/
[3]:https://pcarleton.github.io/2017/3/27/google-sign-in.html