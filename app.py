from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

# Routes
@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return 'Username and password cannot be empty'

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            return 'User already exists'

        new_user = User(username=username, password=password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect('/login')
        except Exception as e:
            return f'Error: {str(e)}'

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect('/chat')
        else:
            return 'Invalid Credentials!'
    return render_template('login.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        content = request.form['content']
        new_message = Message(user_id=session['user_id'], content=content)

        try:
            db.session.add(new_message)
            db.session.commit()
            return redirect('/chat')
        except:
            return 'There was an issue sending your message'
    else:
        messages = Message.query.order_by(Message.date_created).all()
        return render_template('chat.html', messages=messages)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'user_id' not in session:
        return redirect('/login')

    msg = Message.query.get_or_404(id)
    if msg.user_id != session['user_id']:
        return 'You are not authorized to update this message.'

    if request.method == 'POST':
        msg.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/chat')
        except:
            return 'There was an issue updating your message'
    else:
        return render_template('update.html', msg=msg)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    msg_to_delete = Message.query.get_or_404(id)
    if msg_to_delete.user_id != session['user_id']:
        return 'You are not authorized to delete this message.'

    try:
        db.session.delete(msg_to_delete)
        db.session.commit()
        return redirect('/chat')
    except:
        return 'There was a problem deleting your message'

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
