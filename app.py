import os
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy import desc
from db import DATABASE
import sys

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# engineの設定, dbの情報を取得
engine = create_engine(DATABASE())

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
  
  __tablename__ = 'users'

  id = Column('id', Integer, primary_key=True, autoincrement=True)
  username = Column('username', String(200), unique=False)
  hash = Column('password_hash', String(200), unique=False)
  date = Column('dateofbirth', TIMESTAMP, unique=False)
  
  def __init__(self, id=None, username=None, hash=None, date=None):
    self.id = id
    self.username = username
    self.hash = hash
    self.date = date

class Goal(Base):
  
  __tablename__ = 'goals'

  goal_id = Column('goal_id', Integer, primary_key=True, autoincrement=True)
  user_id = Column('user_id', Integer)
  age = Column('age', Integer, unique=False)
  goal = Column('goal', String(200), unique=False)
  detail = Column('detail', String(200))
  
  def __init__(self, goal_id=None, user_id=None, age=None, goal=None, detail=None):
    self.goal_id = goal_id
    self.user_id = user_id
    self.age = age
    self.goal = goal
    self.detail = detail
    
def main(args):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    main(sys.argv)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'GET':
        user_info = db_session.query(User).filter(User.id == session["user_id"]).all()[0]
        user_date = f'{user_info.date}'
        user_life = [int(user_date[0:4]), int(user_date[0:4])+80, user_date[5:7], user_date[8:10]]
        goals = db_session.query(Goal).filter(Goal.user_id == session["user_id"]).order_by(Goal.age).all()
        return render_template("index.html", user_name=user_info.username, user_life=user_life, goals=goals)

    else:
        age = request.form.get('age')
        goal = request.form.get('goal')
        detail = request.form.get('detail')

        new_goal = Goal(user_id=session["user_id"], age=age, goal=goal, detail=detail)
             
        db_session.add(new_goal)
        db_session.commit()
        return redirect('/')


@app.route("/create")
def create():
        return render_template("create.html")

@app.route('/delete/<int:id>')
def delete(id):
    post = Goal.query.get(id)

    db_session.delete(post)
    db_session.commit()
    return redirect('/')

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        rows = db_session.query(User).filter(User.username == request.form.get("username")).all()

        if len(rows) != 1 or not check_password_hash(rows[0].hash, request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0].id

        return redirect("/")
    
    else:
        users = db_session.query(User).all()
        return render_template("login.html", users=users)


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("No username entered!")

        if db_session.query(User).filter(User.username == username).all():
            return apology("Sorry! That username already exists!")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        dateofbirth = request.form.get("dateofbirth")

        if not password or not confirmation or password != confirmation:
            return apology("Please check password!")

        user_name = User()
        user_name.username = username
        user_name.hash = generate_password_hash(password)
        user_name.date = dateofbirth
        db_session.add(user_name)
        db_session.commit()
        return redirect("/login")

    else:
        return render_template("register.html")