import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text

import pandas as pd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

## db
user = 'root'
password = 'eito8110'
host = 'localhost'
db_name = 'life_time'

# engineの設定
engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{db_name}')

# セッションの作成
db_session = scoped_session(
  sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
  )
)

# テーブルを作成する
Base = declarative_base()
Base.query  = db_session.query_property()

# テーブルを定義する
# Baseを継承
class User(Base):
  
  # テーブル名
  __tablename__ = 'users'
  # カラムの定義
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String(100), unique=False)
  hash = Column(Integer, unique=False)
  date = Column(Text, unique=False)
  
  def __init__(self, name=None, hash=None, date=None):
    self.name = name
    self.hash = hash
    self.date = date
    

Base.metadata.create_all(bind=engine)

def read_data():
  """CSVファイルを読み込み、DBにデータを追加する関数
  """
  user_df = pd.read_csv('./data/user.csv')

  for index, _df in user_df.iterrows():
    row = User(name=_df['name'], hash=_df['hash'], date=_df['date'])
    # データを追加する
    db_session.add(row)

  db_session.commit()

read_data()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_info = db_session.query(User).filter(User.id == session["user_id"]).all()

    return render_template("index.html", user_info=user_info[0])


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
        rows = db_session.query(User).filter(User.id == request.form.get("username")).all()

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
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("No username entered!")

        if db_session.query(User).filter(User.name == username).all():
            return apology("Sorry! That username already exists!")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        dateofbirth = request.form.get("dateofbirth")

        if not password or not confirmation or password != confirmation:
            return apology("Please check password!")

        user_name = User()
        user_name.name = username
        user_name.hash = generate_password_hash(password)
        user_name.date = dateofbirth
        db_session.add(user_name)
        db_session.commit()
        return redirect("/login")

    else:
        return render_template("register.html")