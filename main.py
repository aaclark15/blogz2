from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:lcunit2@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'hj67uIj9'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner): 
        self.title = title
        self.body = body
        self.owner = owner


class User(db.Model): 

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref = 'owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


#use function to validate registration info
def is_valid(str1): 
    if str1 == "" or len(str1)<3 or len(str1)>20 or " " in str1: 
        error = True
    else: 
        error = False
    return error    


@app.before_request #run this before calling handler for request
def require_login():
    allowed_routes = ['login', 'index', 'signup', 'display', 'blog_list', 'user_blogs']
    if request.endpoint not in allowed_routes and 'username' not in session: 
        return redirect('/login')


@app.route("/login", methods=['POST', 'GET'])
def login(): 
    if request.method == "POST": 
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username = username).first()
        if user and check_pw_hash(password, user.pw_hash): 
            
            session['username'] = username
            flash('Logged in')
            return redirect('/newpost')
        else: 
            flash('User password incorrect, or user does not exist', 'error')   

    return render_template('login.html')


@app.route("/signup", methods=['POST', 'GET'])
def signup(): 
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        pwd_error = is_valid(password) 
        
        if username !="" and not pwd_error and (verify == password): 

            existing_user = User.query.filter_by(username = username).first()
            if not existing_user: 
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                #remember the user
                session['username'] = username

                return redirect('/newpost')
            else: 
                flash("Duplicate User", 'error')
    
        else: 
            flash("User email or password not valid", 'error')

    return render_template('signup.html')    


@app.route('/logout') 
def logout():
    del session['username']
    return redirect('/')   


@app.route('/blog', methods=['POST', 'GET'])
def blog_list(): 
    
    blogs = Blog.query.all()
    users = User.query.all()

    return render_template('blog_list.html', 
        blogs = blogs, users = users) 


@app.route('/', methods=['POST', 'GET'])
def index(): 
    
    users = User.query.all()

    return render_template('index.html', title = "Blogz", 
        users = users) 


@app.route('/newpost', methods=['POST', 'GET'])
def add_blog():

    owner = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST': 
        title = request.form['title']
        body = request.form['body']

        if title != "" and body != "": 
            new_blog = Blog(title, body, owner)
            db.session.add(new_blog)
            db.session.commit()

            blogs = Blog.query.filter_by(id = new_blog.id, owner=owner).all()
            users = User.query.all()
            return render_template('display.html', blogs = blogs, users = users)
        
        else: 
            flash("Blog post cannot be empty", 'error')
    
    return render_template('newpost.html')

@app.route('/display', methods = ['GET'])
def display():
    blog_id = request.args.get('id')
    id = int(blog_id)

    blogs = Blog.query.filter_by(id = id).all()
    users = User.query.all()

    return render_template('display.html', blogs = blogs, users = users)


@app.route('/user_blogs', methods = ['GET'])
def user_blogs():
    user_id = request.args.get('id')
    id = int(user_id)

    blogs = Blog.query.filter_by(owner_id = id).all()
    users = User.query.filter_by(id = id).all()

    return render_template('user_blogs.html', blogs = blogs, users = users)


if __name__ == '__main__':
    app.run()