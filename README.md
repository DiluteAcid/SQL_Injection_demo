# SQL Injection Demonstration and Defence

This project demonstrates SQL injection vulnerabilities in a Flask web application and shows how to implement defensive measures to prevent these attacks.

## Project Structure

- `app.py`: The main Flask application file
- `users.db`: SQLite database file (created when the app runs)

## Setup and Running

1. Install dependencies:

   ```cmd
   pip install flask flask-sqlalchemy flask-wtf
   ```

2. Run the application:

    ```cmd
    python app.py
    ```

3. Manual SQL Injection Demonstration

   a. Login Bypass:

      - Access http://localhost:5000/login

      - Enter username: `admin' --`

      - Enter any password

      - Click Login

      Expected result: You should be logged in as admin without knowing the password.

      Explanation: The input `admin' --` changes the SQL query to:

   ```sql
   SELECT * FROM user WHERE username = 'admin' -- ' AND password = 'anything'
   ```

   The `--` comments out the rest of the query, bypassing the password check.

   b. Union-based Injection:
      - Access http://localhost:5000/search
      - Enter search term: `' UNION SELECT username, password FROM user --`

      Expected result: You should see a list of all usernames and passwords.

      Explanation: This injection changes the query to:

   ```sql
   SELECT * FROM user WHERE username LIKE '%' UNION SELECT username, password FROM user --%'
   ```

    c. Boolean-based Blind Injection:
  
     - Access http://localhost:5000/search
  
     - Enter search term: `' AND (SELECT SUBSTR(password,1,1) FROM user WHERE username='admin')='s`
  
      Expected result: If the first character of admin's password is 's', you'll see results. If not, you'll see no results.
  
      Explanation: This injection allows you to guess the password one character at a time. You'd need to repeat this process for each character position and possible character.


    d. Automated SQL Injection with SQLmap
  
     ```cmd
     sqlmap -u "http://localhost:5000/login" --data="username=admin&password=password" -p username --dbs
     ```
  
     Expected output: SQLmap should detect that the username parameter is vulnerable to SQL injection and attempt to retrieve database information.

   
     Run SQLmap against the search page:
  
     ```cmd
     sqlmap -u "http://localhost:5000/search" --data="search=test" -p search --dump
     ```
  
      Expected output: SQLmap should detect the vulnerability and attempt to dump the contents of the database.




## Vulnerabilities Exploration

### 1. Database Setup:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
```

This defines our User model. It's not inherently vulnerable, but it's the structure an attacker would try to exploit.

### 2. Vulnerable Login Route:

```python
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
```

This login route is vulnerable because it directly interpolates user input into the SQL query string. An attacker can inject additional SQL commands by manipulating the username or password fields.

For example, entering `admin'--` as the username would change the query to:

```sql
SELECT * FROM user WHERE username = 'admin'--' AND password = 'anything'
```

The `--` comments out the rest of the query, allowing login as admin without a password.

### 3. Vulnerable Search Route:

```python
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_term = request.form['search']
        
        # Vulnerable query
        query = f"SELECT * FROM user WHERE username LIKE '%{search_term}%'"
        print("Executing query:", query)  # Debug print
        result = db.session.execute(text(query))
        results = result.fetchall()
```

This search route is also vulnerable because it directly interpolates the search term into the SQL query. An attacker can inject additional SQL to manipulate the query's behaviour.

For example, entering `' UNION SELECT id, username, password, email, role FROM user --` would change the query to:

```sql
SELECT * FROM user WHERE username LIKE '%' UNION SELECT id, username, password, email, role FROM user --%'
```

This would return all user data, including passwords.

### 4. Debug Printing:

```python
print("Executing query:", query)  # Debug print
```

While not a vulnerability itself, this debug printing allows an attacker (or in this case, you as the demonstrator) to see exactly how the input is affecting the SQL query. In a real application, this kind of debug information should never be visible to users.

### 5. Lack of Input Validation and Sanitization:

The application doesn't perform any input validation or sanitization. It directly uses the user input in SQL queries, which is the root cause of SQL injection vulnerabilities.

### 6. Direct Display of User Data:

```python
return f"Welcome, {username}! Your role is: {user.role}"
```

This directly displays user data. While not an SQL injection vulnerability, it could lead to information disclosure if combined with SQL injection.

### 7. The `/users` Route:

```python
@app.route('/users')
def users():
    users = User.query.all()
    return render_template_string('''
        <h2>All Users:</h2>
        {% for user in users %}
            <p>{{ user.username }} ({{ user.email }}) - {{ user.role }}</p>
        {% endfor %}
    ''', users=users)
```

This route isn't vulnerable to SQL injection (it uses SQLAlchemy's ORM), but it demonstrates poor security practice by exposing all user data. In a real application, this would be a serious privacy and security issue.



## Defensive Measures

The secured version implements the following defensive measures:

### 1. Flask-WTF for Form Handling

```python
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=80)])
    password = StringField('Password', validators=[DataRequired(), Length(min=1, max=120)])

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired(), Length(min=1, max=80)])
```

- Flask-WTF provides CSRF protection out of the box.
- It allows for easy form validation using WTForms validators.
- `DataRequired()` ensures that the field is not empty.
- `Length(min=1, max=80)` restricts the input length, preventing overly long inputs that could be used in attacks.

### 2. Parameterized Queries

```python
# Secure query using SQLAlchemy ORM
user = User.query.filter_by(username=username, password=password).first()

# Secure query using SQLAlchemy ORM
results = User.query.filter(User.username.like(f'%{search_term}%')).all()
```

- Instead of constructing SQL queries with string concatenation, we use SQLAlchemy's ORM methods.
- These methods automatically use parameterized queries, which separate the SQL command from the data.
- This prevents SQL injection by ensuring that user input is always treated as data, not part of the SQL command.

### 3. Input Validation

```python
if form.validate_on_submit():
    username = form.username.data
    password = form.password.data
```

- `validate_on_submit()` checks if the form is submitted and valid according to the defined validators.

- This ensures that the input meets the criteria we've set (not empty, within length limits) before we process it.

### 4. SQL Injection Detection Middleware

```python
@app.before_request
def check_for_sql_injection():
    for key, value in request.form.items():
        if any(char in value for char in "';--\""):
            abort(403, description="Potential SQL injection detected")
```

- This middleware function runs before each request.

- It checks all form inputs for common SQL injection characters.
- If any are found, it aborts the request with a 403 Forbidden error.
- While this is a simple check and not fool proof, it adds an extra layer of defence. 

### 5. Removal of String Interpolation in Queries

We've completely removed instances of string formatting in SQL queries, like:

``` python
query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
```

These have been replaced with ORM methods, eliminating the possibility of SQL injection through string interpolation.

### 6. Use of ORM Methods

```python
user = User.query.filter_by(username=username, password=password).first()
results = User.query.filter(User.username.like(f'%{search_term}%')).all()
```

- SQLAlchemy's ORM methods are used instead of raw SQL.
- These methods handle the SQL generation and ensure proper escaping of parameters.
- They provide an abstraction layer that helps prevent SQL injection vulnerabilities.

## Additional Security Considerations

1. **Secret Key**:  This is required for CSRF protection. In a real application, this should be a strong, randomly generated key stored securely.

   ```python
   app.config['SECRET_KEY'] = 'your-secret-key'
   ```

2. **CSRF Protection**: Flask-WTF automatically adds CSRF protection. In the template, we include the CSRF token:

   ```html
   {{ form.csrf_token }}
   ```

3. **Password Security**: While not implemented in this demo for simplicity, in a real application, passwords should never be stored in plain text. They should be hashed using a strong algorithm like bcrypt.

4. **HTTPS**: While not shown in the code, all production applications should use HTTPS to encrypt data in transit.






## Disclaimer

This project is for educational purposes only. The vulnerable version should never be used in a production environment.



## Contributing

Contributions to improve the demonstration or add additional security measures are welcome. Please submit a pull request or open an issue to discuss proposed changes.
