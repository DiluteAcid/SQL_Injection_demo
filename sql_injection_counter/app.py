from flask import Flask, request, render_template_string, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Required for CSRF protection
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

with app.app_context():
    db.create_all()
    # Add sample users if the database is empty
    if not User.query.first():
        sample_users = [
            User(username='admin', password='secretpassword', email='admin@example.com', role='admin'),
            User(username='john_doe', password='password123', email='john@example.com', role='user'),
            User(username='jane_smith', password='securepass', email='jane@example.com', role='user'),
            User(username='bob_johnson', password='bobpass', email='bob@example.com', role='user'),
            User(username='alice_wonder', password='alicepass', email='alice@example.com', role='user'),
            User(username='charlie_brown', password='snoopy', email='charlie@example.com', role='user'),
            User(username='emma_watson', password='hermione', email='emma@example.com', role='user'),
            User(username='david_beckham', password='football', email='david@example.com', role='user'),
            User(username='sarah_connor', password='terminator', email='sarah@example.com', role='user'),
            User(username='tony_stark', password='ironman', email='tony@example.com', role='user'),
        ]
        
        # Add 20 more random users
        for i in range(20):
            username = f"user_{generate_random_string(5)}"
            password = generate_random_string(10)
            email = f"{username}@example.com"
            role = random.choice(['user', 'moderator'])
            sample_users.append(User(username=username, password=password, email=email, role=role))
        
        db.session.add_all(sample_users)
        db.session.commit()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=80)])
    password = StringField('Password', validators=[DataRequired(), Length(min=1, max=120)])

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired(), Length(min=1, max=80)])

@app.before_request
def check_for_sql_injection():
    for key, value in request.form.items():
        if any(char in value for char in "';--\""):
            abort(403, description="Potential SQL injection detected")

@app.route('/')
def index():
    return "Welcome to the SQL Injection Demo (Secure Version)"

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Secure query using SQLAlchemy ORM
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            return f"Welcome, {username}! Your role is: {user.role}"
        else:
            return "Login failed."
    
    return render_template_string('''
        <form method="post">
            {{ form.csrf_token }}
            Username: {{ form.username }}<br>
            Password: {{ form.password }}<br>
            <input type="submit" value="Login">
        </form>
    ''', form=form)

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        search_term = form.search.data
        
        # Secure query using SQLAlchemy ORM
        results = User.query.filter(User.username.like(f'%{search_term}%')).all()
        
        return render_template_string('''
            <h2>Search Results:</h2>
            {% for user in results %}
                <p>{{ user.username }} ({{ user.email }}) - {{ user.role }}</p>
            {% endfor %}
            <a href="/search">Back to Search</a>
        ''', results=results)
    
    return render_template_string('''
        <form method="post">
            {{ form.csrf_token }}
            Search: {{ form.search }}
            <input type="submit" value="Search">
        </form>
    ''', form=form)

@app.route('/users')
def users():
    users = User.query.all()
    return render_template_string('''
        <h2>All Users:</h2>
        {% for user in users %}
            <p>{{ user.username }} ({{ user.email }}) - {{ user.role }}</p>
        {% endfor %}
    ''', users=users)

if __name__ == '__main__':
    app.run(debug=True)
