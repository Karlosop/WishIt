
from flask import redirect, render_template, request, session
from functools import wraps

def apology(message):
    """Render message as an apology to user."""
    print(message)
    return render_template("apology.html", value=message)


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function