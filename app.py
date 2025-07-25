from flask import Flask,redirect,render_template,request,url_for
from flask.globals import request, session
from flask_sqlalchemy import SQLAlchemy
from flask import flash
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,login_manager,UserMixin,LoginManager,login_required,logout_user
import os
from werkzeug.utils import secure_filename
from datetime import datetime

local_server=True
app=Flask(__name__)
app.secret_key="govindkumarsahu@122345"


login_manager=LoginManager(app)
login_manager.login_view='login'

#Database configuration
# aap.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://root:Govind#sahu098@localhost/socialmedia'
db=SQLAlchemy(app)

# configuration for heandling files
app.config['UPLOAD_FOLDER']='static/uploads/'
app.config['ALLOWED_EXTENSION']={'png','jpg','jpeg','gif'}
app.config['MAX_CONTENT_LENGTH']=16*1024*1024 # 16mbmax upload size

@login_manager.user_loader
def load_user(user_id):
    return Signup.query.get(int(user_id))

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# initalise the signup model 
class Signup(UserMixin,db.Model):
    user_id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String(50))
    last_name=db.Column(db.String(50))
    email=db.Column(db.String(100))
    password=db.Column(db.String(1000),unique=True)
    phone=db.Column(db.Integer,unique=True)

    def get_id(self):
        return self.user_id
    

class Posts(db.Model):
    post_id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(50))
    title=db.Column(db.String(100))
    description=db.Column(db.String(500))   
    image=db.Column(db.String(500))
    date=db.Column(db.String(500))
    time=db.Column(db.String(500))
    likes=db.Column(db.Integer,nullable=True)

class Comments(db.Model):
    comment_id=db.Column(db.Integer,primary_key=True)
    post_id=db.Column(db.Integer)
    comment=db.Column(db.String(500))
    commentedBy=db.Column(db.String(100))
    commentedOn=db.Column(db.String(100))

class Friends(db.Model):
    friends_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer)
    requested_id=db.Column(db.Integer)
    isAccepted=db.Column(db.String(10))

@app.route("/")
def index():
    data=Posts.query.all()
    return render_template("index.html",data=data)

@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method=="POST":
        firstName=request.form.get("fname")
        lastName=request.form.get("lname")
        email=request.form.get("email")
        phoneNumber=request.form.get("phone")
        password=request.form.get("pass1")
        conformPassword=request.form.get("pass2")
        print(firstName,lastName,email,phoneNumber,password,conformPassword)
        if password != conformPassword:
            flash("password is not matching","warning")
            return redirect(url_for("signup"))

        fetchemail=Signup.query.filter_by(email=email).first()
        fetchphone=Signup.query.filter_by(email=phoneNumber).first() 
        if fetchemail or fetchphone:
            flash("User exist alredy","warning")
            return redirect(url_for("signup"))
        
        if len(phoneNumber)!=10:
            flash("Please enter 10 digit number")
            return redirect(url_for("signup"))
        gen_pass=generate_password_hash(password)
        query=f"INSERT into `signup` (`first_name`,`last_name`,`email`,`password`,`phone`) VALUE ('{firstName}','{lastName}','{email}','{gen_pass}','{phoneNumber}')"
        with db.engine.begin() as conn:
            response=conn.exec_driver_sql(query)
            flash("Signup Success","success")
            return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=['GET','POST'])
def login():
     if request.method=="POST":
         email=request.form.get("email")
         password=request.form.get("pass1")
         user=Signup.query.filter_by(email= email).first()
         if user and check_password_hash(user.password,password):
             login_user(user)
             flash("login success","success")
             return render_template("index.html")
         else:
             flash("Invalid Credentials","info")
             return render_template("login.html")
     return render_template("login.html") 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Success","primary")
    return redirect(url_for('login'))

@app.route("/test/")
def test():
    try:
        # query=Test.query.all()
        # print(query)
        sql_query="select * from test"
        with db.engine.begin() as conn:
            response=conn.exec_driver_sql(sql_query).all()
            print(response)
        return" Database is connected"
    except Exception as e:
        return "Database is not connected,{e}"
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSION']     
    
@app.route("/posts", methods=['GET','POST'])
def posts():
    if request.method=='POST':
        email=request.form['email']
        title=request.form['title']
        description=request.form['description']
        file=request.files['image']
        date=datetime.now()
        datee=date.date()
        time=date.time()
        if file and allowed_file(file.filename):
            # save the file name in the uploads folder
            filename=secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

            # write the query to save iin db
            query=Posts(email=email,title=title,description=description,image=file.filename,date=datee,time=time)
            db.session.add(query)
            db.session.commit()
            flash("Post is uploaded","info")
            return redirect(url_for('index'))
        else:
            flash("Please use 'png','jpg','jpeg','gif',file format","warning")

    return render_template("posts.html")

# logic for likes
@app.route('/like/<int:id>',methods=['GET',"POST"])
def like(id):
    post=Posts.query.filter_by(post_id=id).first()
    if post.likes==None:
        post.likes=1
        db.session.commit()
    post.likes=post.likes+1
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/comment/<int:id>',methods=['GET',"POST"])
def comment(id):
      if request.method=='POST':
        comment=request.form['comment']
        commentedBy=request.form['commented']
        commentedOn=datetime.now()
        query=Comments(post_id=id,comment=comment, commentedBy=commentedBy,commentedOn=commentedOn)
        db.session.add(query)
        db.session.commit()
        flash("Comment Added","success")
        return redirect(url_for('index'))
      

@app.route('/viewcomment/<int:id>',methods=['GET','POST'])
def viewcomment(id):
    post=Comments.query.filter_by(post_id=id).all()     
    return render_template("comments.html",post=post) 


@app.route('/connect',methods=['GET','POST'])
def connect():   
    return render_template("connect.html") 