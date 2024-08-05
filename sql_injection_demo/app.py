from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

@app.route('/')
def index():
    return "Welcome to the SQL Injection Demo"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Vulnerable query
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
        print("Executing query:", query)  # Debug print
        result = db.session.execute(text(query))
        user = result.fetchone()
        
        if user:
            return f"Welcome, {username}! Your role is: {user.role}"
        else:
            return "Login failed."
    
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search']
        
        # Vulnerable query
        query = f"SELECT * FROM user WHERE username LIKE '%{search_term}%'"
        print("Executing query:", query)  # Debug print
        result = db.session.execute(text(query))
        results = result.fetchall()
        
        return render_template_string('''
            <h2>Search Results:</h2>
            {% for user in results %}
                <p>{{ user.username }} ({{ user.email }}) - {{ user.role }}</p>
            {% endfor %}
            <a href="/search">Back to Search</a>
        ''', results=results)
    
    return render_template_string('''
        <form method="post">
            Search: <input type="text" name="search">
            <input type="submit" value="Search">
        </form>
    ''')

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
