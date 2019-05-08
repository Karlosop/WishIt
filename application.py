from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
#from flask_table import Table, Col
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# nerozumim Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# nerozumim Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///gifts.db")



#----------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------

@app.route("/")
@login_required
def index():
    return redirect("/users")

@app.route("/my_wishlist", methods=["GET", "POST"])
@login_required
def my_wishlist():
    #shows user his current wishlist (on get) and allows to add to it (via post)



    if request.method == "GET":
        wishlist = db.execute('SELECT * FROM wishes WHERE user_id = (:user_id)', user_id = session["user_id"])
        return render_template("my_wishlist.html", wishlist = wishlist)

    else:   #insert the wish into the database
        if not request.form.get('wish_name'):
            return apology('Zadej prosím, co si přeješ.')

        db.execute('INSERT INTO wishes (user_id, wish_name, wish_description) VALUES (:user_id, :wish_name, :wish_description)', user_id = session["user_id"], wish_name = request.form.get('wish_name'), wish_description = request.form.get('wish_description'))
        wishlist = db.execute('SELECT * FROM wishes WHERE user_id = (:user_id)', user_id = session["user_id"])
        return render_template("my_wishlist.html", wishlist = wishlist)

@app.route("/add_user_wish/<user_id>", methods=["GET", "POST"])
@login_required
def add_user_wish(user_id):
    #shows or submits a form to add a new wish

    if request.method == "GET":
        user_name = db.execute('SELECT user_name FROM users WHERE user_id = (:user_id)', user_id = user_id)
        user_name = user_name[0]['user_name']
        return render_template("add_user_wish.html", user_name = user_name)

    else:   #insert the wish into the database
        if not request.form.get('wish_name'):
            return apology('Zadej prosím, co si přeješ.')

        db.execute('INSERT INTO wishes (user_id, wish_name, wish_description, wish_originator_id) VALUES (:user_id, :wish_name, :wish_description, :wish_originator_id)',\
        user_id = user_id, wish_name = request.form.get('wish_name'), wish_description = request.form.get('wish_description'), wish_originator_id = session['user_id'])
        wishlist = db.execute('SELECT * FROM wishes WHERE user_id = (:user_id)', user_id = session["user_id"])
        path = '/user/' + str(user_id)
        return redirect(path)

@app.route("/users")
@login_required
def users():
    names = db.execute('SELECT * FROM users WHERE user_id <> (:user_id)', user_id = session["user_id"])

    return render_template("users.html", names = names)

@app.route("/my_dibs")
@login_required
def my_dibs():
    dibs = db.execute('SELECT * FROM wishes WHERE wish_dibs = (:my_id)', my_id = session['user_id'])
    for dib in dibs:
        temp = db.execute('SELECT user_name FROM users WHERE user_id = (:user_id)', user_id = dib['user_id'])
        dib['user_name'] = temp[0]['user_name']
    return render_template("my_dibs.html", dibs = dibs)

@app.route('/user/<user_id>')
@login_required
def user(user_id):
    wishes = db.execute('SELECT * FROM wishes WHERE user_id = (:user_id)', user_id = user_id)
    for wish in wishes:
        if wish['wish_dibs'] is None:
            wish['wish_dibs'] = 'Zamluvit!'
        else:
            #change the user id in wish to user name
            diber_name = db.execute('SELECT user_name FROM users WHERE (:user_id) = user_id', user_id = wish['wish_dibs'])
            diber_name = diber_name[0]['user_name']
            wish['wish_dibs'] = diber_name

    user_info = db.execute('SELECT * FROM users WHERE user_id = (:user_id)', user_id = user_id)
    user_info = user_info[0]
    my_name = session['user_name']
    return render_template('user.html', wishes = wishes, user_info = user_info, my_name = my_name)

@app.route('/call_dibs/<wish_id>')
@login_required
# will call dibs on selected wish for logged user
def call_dibs(wish_id):
    check_dibed = db.execute('SELECT wish_dibs, user_id FROM wishes WHERE wish_id = (:wish_id)', wish_id = wish_id)
    check_dibed = check_dibed[0]

    #check if the someone already called dibs (against URL injection)
    if check_dibed['wish_dibs'] is None:

        # inserd the dib record into db
        db.execute('UPDATE wishes SET wish_dibs = (:user_id) WHERE wish_id = (:wish_id)', wish_id = wish_id, user_id = session["user_id"])

        # return user to the updated user/# page
        redirect_adress = '/user/' + str(check_dibed["user_id"])
        return redirect(redirect_adress)
    else:
        return apology('Chyba: prani uz je zamluveno')

@app.route('/undib/<wish_id>')
@login_required
# will cancel dibs on selected wish for logged user
def undib(wish_id):
    check_dibed = db.execute('SELECT wish_dibs, user_id FROM wishes WHERE wish_id = (:wish_id)', wish_id = wish_id)
    check_dibed = check_dibed[0]
    #check if dibs in db is for logged user (against URL injection)
    if check_dibed['wish_dibs'] == session['user_id']:

        #change dibs value to NULL
        db.execute('UPDATE wishes SET wish_dibs = NULL WHERE wish_id = (:wish_id)', wish_id = wish_id)

        # return user to the updated user/# page
        redirect_adress = '/user/' + str(check_dibed["user_id"])
        return redirect(redirect_adress)
    else:
        return apology("Chyba, přání nebylo zamluveno Vámi")



@app.route('/wish/<wish_id>')
@login_required
# shows a page with wish details
def wish(wish_id):
    wish_details = db.execute('SELECT * FROM wishes WHERE wish_id = (:wish_id)', wish_id = wish_id)
    wish_details = wish_details[0]

    #change the user id in wish to user name
    temp = db.execute('SELECT user_name FROM users WHERE (:user_id) = user_id', user_id = wish_details['wish_dibs'])
    if temp:
        temp = temp[0]['user_name']
        wish_details['wish_dibs'] = temp
    else:
        wish_details['wish_dibs'] = 'None'
    temp = db.execute('SELECT user_name FROM users WHERE (:user_id) = user_id', user_id = wish_details['user_id'])
    temp = temp[0]['user_name']
    wish_details['user_id'] = temp

    if wish_details['user_id'] == session['user_name']:
        return render_template('my_wish.html', wish = wish_details)
    else:
        return render_template('wish.html', wish = wish_details)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

   # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Zadej prosím jméno")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Zadej heslo")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE user_name = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Chybné jméno nebo heslo")

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session["user_name"] = rows[0]["user_name"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """ Log User out """

    # Forget any user_id
    session.clear()

    # Redirect user to home page
    return apology("Byl/a jsi odhlášen/a.")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        #do stuff (confirm submited data and if correct, register)

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Nebylo zadáno jméno")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Nebylo zadáno heslo")

        # Ensure password was confirmed
        elif not request.form.get("password_confirm"):
            return apology("Nebylo zadáno ověření hesla")

        # Ensure password and confirmation match
        elif not (request.form.get("password") == request.form.get("password_confirm")):
            return apology("Heslo a ověření hesla nejsou shodné")

        #hash password
        hashedpw = generate_password_hash(request.form.get("password"))

        # insert into database

        db.execute("INSERT INTO users (user_name, hash, user_bday, user_nday) VALUES (:name, :hash, :user_bday, :user_nday)", hash = hashedpw, name = request.form.get("username"), user_bday = request.form.get("b_day"), user_nday = request.form.get("n_day"))

        #log user in   # Remember which user has logged in        session["user_id"] = rows[0]["id"]
        uid = db.execute("SELECT user_id FROM users WHERE user_name = (:username)", username = request.form.get("username"))

        session["user_id"] = uid[0]["user_id"]
        session["user_name"] = request.form.get("username")


        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")