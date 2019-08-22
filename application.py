import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
#from flask_table import Table, Col
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application and database
app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(160))
    user_bday = db.Column(db.String(26))
    user_nday = db.Column(db.String(26))

class Wishes(db.Model):
    wish_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    wish_name = db.Column(db.String(80), nullable=False)
    wish_dibs = db.Column(db.Integer)
    wish_description = db.Column(db.String(1000))
    wish_originator_id = db.Column(db.Integer)
    diber_name = db.Column(db.String(80))

# nerozumim Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# nerozumim Configure session to use filesystem (instead of signed cookies)
#app.config["SESSION_FILE_DIR"] = mkdtemp()
#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_TYPE"] = "memcached"
app.config["SECRET_KEY"] = "rY6YDbCp*vKxK6qzp4*Z#"
sess = Session()
#Session(app)






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
        
        wishlist=Wishes.query.filter_by(user_id=session['user_id'])

        return render_template("my_wishlist.html", wishlist = wishlist)

    else:   #insert the wish into the database
        if not request.form.get('wish_name'):
            return apology('Zadej prosím, co si přeješ.')

        new_wish = Wishes(user_id=session["user_id"], wish_name=request.form.get('wish_name'), wish_description=request.form.get('wish_description'))
        db.session.add(new_wish)
        db.session.commit()        
        
        wishlist=Wishes.query.filter_by(user_id=session['user_id'])

        return render_template("my_wishlist.html", wishlist = wishlist)




@app.route("/add_user_wish/<user_id>", methods=["GET", "POST"])
@login_required
def add_user_wish(user_id):
    #shows or submits a form to add a new wish

    if request.method == "GET":
        #user_name = db.execute('SELECT user_name FROM users WHERE user_id = (:user_id)', user_id = user_id)
        user = Users.query.filter_by(user_id=user_id).first()
        return render_template("add_user_wish.html", user_name = user.user_name)

    else:   #insert the wish into the database
        if not request.form.get('wish_name'):
            return apology('Zadej prosím, co si přeješ.')

        new_wish = Wishes(user_id=user_id, wish_name=request.form.get('wish_name'), wish_description=request.form.get('wish_description'), wish_originator_id=session['user_id'])
        db.session.add(new_wish)
        db.session.commit()
     
        path = '/user/' + str(user_id)
        return redirect(path)



@app.route("/users")
@login_required
def users():
    
    names = Users.query.all()
    
    #remove the data of logged user from the list
    for name in names:
        if name.user_name == session['user_name']:
            names.remove(name)

    return render_template("users.html", names = names)



@app.route("/my_dibs")
@login_required
def my_dibs():
    
    dibs = Wishes.query.filter_by(wish_dibs=session['user_id']).all()
    #tohle je trochu prasárna, ale bez commitu tu nahrazuju diber name usernamem přejícího si jen pro účely templatu my_dibs.html
    for dib in dibs:
        temp = Users.query.filter_by(user_id=dib.user_id).first()
        dib.diber_name = temp.user_name
    return render_template("my_dibs.html", dibs = dibs)



@app.route('/user/<user_id>')
@login_required
def user(user_id):
    
    wishes = Wishes.query.filter_by(user_id=user_id).all()
    
    
    user_info = Users.query.filter_by(user_id=user_id).first()
    my_name = session['user_name']
    return render_template('user.html', wishes = wishes, user_info = user_info, my_name = my_name)


@app.route('/call_dibs/<wish_id>')
@login_required
# will call dibs on selected wish for logged user
def call_dibs(wish_id):
    
    check_dibed = Wishes.query.filter_by(wish_id=wish_id).first()
    

    #check if the someone already called dibs (against URL injection)
    if check_dibed.wish_dibs is None:

        
        # inserd the dib record into db
        
        check_dibed.wish_dibs = session['user_id']
        check_dibed.diber_name = session['user_name']
        db.session.commit()

        # return user to the updated user/# page
        redirect_adress = '/user/' + str(check_dibed.user_id)
        return redirect(redirect_adress)
    else:
        return apology('Chyba: prani uz je zamluveno')




@app.route('/undib/<wish_id>')
@login_required
# will cancel dibs on selected wish for logged user
def undib(wish_id):
    
    check_dibed = Wishes.query.filter_by(wish_id=wish_id).first()
    #check if dibs in db is for logged user (against URL injection)
    if check_dibed.wish_dibs == session['user_id']:

        #change dibs value to NULL
        
        check_dibed.wish_dibs = None
        check_dibed.diber_name = None
        db.session.commit()

        # return user to the updated user/# page
        redirect_adress = '/user/' + str(check_dibed.user_id)
        return redirect(redirect_adress)
    else:
        return apology("Chyba, přání nebylo zamluveno Vámi")


@app.route('/wish/<wish_id>')
@login_required
# shows a page with wish details
def wish(wish_id):
       
    wish_details = Wishes.query.filter_by(wish_id=wish_id).first()

    #change the user id in wish to user name
    
    user = Users.query.filter_by(user_id=wish_details.user_id).first()
    originator = Users.query.filter_by(user_id=wish_details.wish_originator_id).first()
    
     

    if user.user_name == session['user_name']:
        return render_template('my_wish.html', wish = wish_details)
    else:
        if originator:
            return render_template('wish.html', wish = wish_details, user_name = user.user_name, viewer_id = session['user_id'], originator = originator.user_name)
        else:
            return render_template('wish.html', wish = wish_details, user_name = user.user_name, viewer_id = session['user_id'])


@app.route('/change_wish/<wish_id>', methods=["GET", "POST"])
@login_required
#changes users wish
def change_wish(wish_id):
    if request.method == "GET":    
        wish_details = Wishes.query.filter_by(wish_id=wish_id).first()
        #protect against URL injections

        if wish_details.user_id == session['user_id']:
            return render_template('change_wish.html', wish = wish_details)
    
        elif wish_details.wish_originator_id == session['user_id']:
            return render_template('change_wish.html', wish = wish_details)

        else:
            return apology('Nemáte oprávnění ke smazání tohoto přání')
    
    #If method was POST, update the wish record in db
    else:
        wish_details = Wishes.query.filter_by(wish_id=wish_id).first()
        wish_details.wish_name = request.form.get('wish_name')
        wish_details.wish_description = request.form.get('wish_description')
        db.session.commit()
        return apology('Přání bylo aktualizováno.')

@app.route('/delete_wish/<wish_id>')
@login_required
#deletes users wish
def delete_wish(wish_id):
    
    wish_details = Wishes.query.filter_by(wish_id=wish_id).first()
    #protect against URL injections

    if wish_details.user_id == session['user_id']:
        db.session.delete(wish_details)
        db.session.commit()
        return apology('Přání bylo smazáno.')
    
    elif wish_details.wish_originator_id == session['user_id']:
        db.session.delete(wish_details)
        db.session.commit()
        return apology('Přání bylo smazáno.')

    else:
        return apology('Nemáte oprávnění ke smazání tohoto přání')


@app.route("/login", methods=["GET", "POST"])
def login():
    #Log user in

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
        
        loginee = Users.query.filter_by(user_name=request.form.get("username")).first()

        # Ensure username exists and password is correct
        if loginee == None or not check_password_hash(loginee.hash, request.form.get("password")):
            return apology("Chybné jméno nebo heslo")

        # Remember which user has logged in
        session["user_id"] = loginee.user_id
        session["user_name"] = loginee.user_name

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Log User out 

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
        hash = generate_password_hash(request.form.get("password"))

        
        # insert into database                    
        new_user = Users(user_name=request.form.get("username"), hash=generate_password_hash(request.form.get("password")), user_bday=request.form.get("b_day"), user_nday=request.form.get("n_day"))
        
        db.session.add(new_user)
        db.session.commit()

        #log user in   # Remember which user has logged in 
           
        user = Users.query.filter_by(user_name=request.form.get("username")).first()
        
        session["user_id"] = user.user_id
        session["user_name"] = request.form.get("username")
        
        print('user name in session is: ', session["user_name"])

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")