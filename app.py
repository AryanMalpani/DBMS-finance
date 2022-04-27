import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

import datetime



# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""


    profile = db.execute("SELECT username, cash FROM users WHERE id = ?", session["user_id"])

    shares = db.execute("SELECT name, symbol, SUM(count) FROM usershares WHERE userid = ? GROUP BY symbol ORDER BY SUM(count) DESC", session["user_id"])

    summary= []

    for share in shares:
        summary.append({
            "name" : share["name"],
            "symbol" : share["symbol"],
            "count" : share["SUM(count)"],
            "prize" : lookup(share["symbol"])["price"],
            "value" : lookup(share["symbol"])["price"]*share["SUM(count)"]})


    return render_template("index.html", summary = summary, profile = profile[0])

    #return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        stock = lookup(request.form.get("symbol"))
        number = float(request.form.get("shares"))
        money = float(db.execute("SELECT cash FROM users WHERE id = ?",session["user_id"])[0]["cash"])



        x = datetime.datetime.now()

        if stock is None or number is None or number == 0 :
            return apology("error in stock name or number of shares", 400)

        if money < stock["price"] * number :
            return apology("lmao paisa nahi hein", 420)


        #if stock["symbol"] not in db.execute("SELECT symbol FROM usershares WHERE userid = ?",session["user_id"]) :
        db.execute("INSERT INTO usershares (userid, name, symbol, count, cost, time) VALUES(?,?,?,?,?,?)", session["user_id"], stock["name"], stock["symbol"], number, stock["price"], x)

        #else:
            #count = db.execute("SELECT count FROM usershares WHERE symbol = ? AND id = ?", stock["symbol"], session["user_id"])[0]["count"]
            #db.execute("UPDATE usershares SET count = ? WHERE symbol = ? AND userid = ?",count + number, stock["symbol"], session["user_id"])

        db.execute("UPDATE users SET cash = ? WHERE id = ?", money - stock["price"] * number, session["user_id"])

        return redirect("/")


    else :
        return render_template("buyhome.html")

    return apology("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    history = db.execute("SELECT * FROM usershares WHERE userid = ?", session["user_id"])

    return render_template("history.html", history = history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        stock = lookup(request.form.get("symbol"))
        if stock is None :
            return apology("Stock Dosen't Exist", "Bhak")

        return render_template("quoted.html", stock = stock)

    else:
        return render_template("quote.html")





@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        username = request.form.get("username")

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",username , generate_password_hash(request.form.get("password")))

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

         # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else :

        return render_template("register.html")

    #return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        stock = lookup(request.form.get("symbol"))
        number =  float(request.form.get("shares"))
        money = float(db.execute("SELECT cash FROM users WHERE id = ?",session["user_id"])[0]["cash"])


        if stock is None or number is None or number < 1 :
            return apology("error in stock name or number of shares", 400)

        #if money < stock["price"] * number :
            #return apology("lmao paisa nahi hein", 420)

        number = -number

        x = datetime.datetime.now()


        db.execute("INSERT INTO usershares (userid, name, symbol, count, cost, time) VALUES(?,?,?,?,?,?)", session["user_id"], stock["name"], stock["symbol"], number, stock["price"], x)


        #count = db.execute("SELECT count FROM usershares WHERE symbol = ? AND id = ?", stock["symbol"], session["user_id"])[0]["count"]
        #db.execute("UPDATE usershares SET count = ? WHERE symbol = ? AND userid = ?",count + number, stock["symbol"], session["user_id"])

        db.execute("UPDATE users SET cash = ? WHERE id = ?", money - (stock["price"] * number), session["user_id"])

        return redirect("/")

    else :
        #sharenames = db.execute("SELECT DISTINCT name, symbol FROM usershares WHERE userid = ?", session["user_id"])
        return render_template("sellhome.html")#, sharenames = sharenames)

    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
