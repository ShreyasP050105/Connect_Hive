from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jit123'
app.config['MYSQL_DB'] = 'connect_hive'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)

# ---------- Routes ----------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password'].encode('utf-8')
        role = request.form['role']

        # check for existing username
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            flash('Username already exists. Please choose another.', 'warning')
            return render_template('register.html')

        # hash password and insert user
        hashed = bcrypt.hashpw(password_input, bcrypt.gensalt())
        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed.decode('utf-8'), role)
            )
            mysql.connection.commit()
            flash('Registration successful! You can now log in.', 'success')
        except Exception as e:
            flash(f'Error registering user: {e}', 'danger')
        finally:
            cur.close()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password_input, user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            if user[3] == 'parent':
                return redirect(url_for('parent_dashboard'))
            elif user[3] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user[3] == 'staff':
                return redirect(url_for('staff_dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/parent_dashboard')
def parent_dashboard():
    if 'user_id' not in session or session.get('role') != 'parent':
        flash("Please login as a parent to access this page", "info")
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name, grade, roll FROM students WHERE parent_id = %s", (user_id,))
    child = cur.fetchone()

    if child:
        child_data = {
            'id': child[0],
            'name': child[1],
            'class': child[2],
            'roll': child[3]
        }

        cur.execute("SELECT subject, marks FROM marks WHERE student_id = %s", (child[0],))
        marks = [{'subject': row[0], 'marks': row[1]} for row in cur.fetchall()]

        cur.execute("SELECT date, subject, content FROM homework WHERE class = %s ORDER BY date DESC", (child[2],))
        homework = [{'date': row[0], 'subject': row[1], 'task': row[2]} for row in cur.fetchall()]

        cur.execute("SELECT sender, message, timestamp FROM chat WHERE child_id = %s ORDER BY timestamp", (child[0],))
        chat_history = [{'sender': row[0], 'message': row[1], 'timestamp': row[2]} for row in cur.fetchall()]
    else:
        child_data = {'name': 'N/A', 'class': 'N/A', 'roll': 'N/A'}
        marks = []
        homework = []
        chat_history = []

    cur.close()
    return render_template('parent_dashboard.html', child=child_data, marks=marks, homework=homework, chat_history=chat_history)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash("Please login as a teacher to access this page", "info")
        return redirect(url_for('login'))

    return render_template('teacher_dashboard.html')



@app.route('/add_homework', methods=['POST'])
def add_homework():
    class_name = request.form['class_name']
    subject = request.form['subject']
    date = request.form['date']
    content = request.form['content']
    # ... your DB insert code here ...

    flash("Homework submitted successfully!", "success")
    return redirect(url_for('teacher_dashboard'))


@app.route('/add_marks', methods=['POST'])
def add_marks():
    try:
        student_name = request.form['student_name']
        subject = request.form['subject']
        marks = request.form['marks']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO marks (student_name, subject, marks) VALUES (%s, %s, %s)",
            (student_name, subject, marks)
        )
        mysql.connection.commit()
        cursor.close()

        flash('Marks added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding marks: {e}', 'danger')
    return redirect(url_for('teacher_dashboard'))


@app.route('/staff_dashboard')
def staff_dashboard():
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Please login as staff to access this page", "info")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Get total students count
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Get total teachers count
    cursor.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = cursor.fetchone()[0]

    # Get class-wise student counts
    cursor.execute("SELECT grade, COUNT(*) FROM students GROUP BY grade ORDER BY grade")
    class_student_counts = cursor.fetchall()  # List of tuples (grade, count)

    cursor.close()

    return render_template(
        'staff_dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        class_student_counts=class_student_counts
    )


@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['student_name']
    class_name = request.form['student_class']
    roll = request.form['student_roll']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (name, grade, roll) VALUES (%s, %s, %s)",
            (name, class_name, roll)
        )
        mysql.connection.commit()
        flash('Student added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding student: {e}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('staff_dashboard'))


@app.route('/delete_student', methods=['POST'])
def delete_student():
    roll = request.form['student_roll']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE roll = %s", (roll,))
        mysql.connection.commit()
        if cursor.rowcount == 0:
            flash('No student found with that roll number.', 'warning')
        else:
            flash('Student deleted successfully!', 'danger')
    except Exception as e:
        flash(f'Error deleting student: {e}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('staff_dashboard'))


@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    name = request.form['teacher_name']
    subject = request.form['teacher_subject']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO teachers (name, subject) VALUES (%s, %s)", (name, subject))
        mysql.connection.commit()
        flash('Teacher added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding teacher: {e}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('staff_dashboard'))


@app.route('/delete_teacher', methods=['POST'])
def delete_teacher():
    name = request.form['teacher_name']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM teachers WHERE name = %s", (name,))
        mysql.connection.commit()
        if cursor.rowcount == 0:
            flash('No teacher found with that name.', 'warning')
        else:
            flash('Teacher deleted successfully!', 'danger')
    except Exception as e:
        flash(f'Error deleting teacher: {e}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('staff_dashboard'))


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session or session.get('role') != 'parent':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    message = request.form['message']
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM students WHERE parent_id = %s", (user_id,))
    child = cur.fetchone()

    if child:
        cur.execute(
            "INSERT INTO chat (child_id, sender, message, timestamp) VALUES (%s, %s, %s, %s)",
            (child[0], 'Parent', message, datetime.datetime.now())
        )
        mysql.connection.commit()

    cur.close()
    flash("Message sent!", "success")
    return redirect(url_for('parent_dashboard'))

@app.route('/clear_chat')
def clear_chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    role = cur.fetchone()

    if not role or role[0] != 'parent':
        return "Unauthorized", 403

    cur.execute("SELECT id FROM students WHERE parent_id = %s", (user_id,))
    child = cur.fetchone()
    if child:
        cur.execute("DELETE FROM chat WHERE child_id = %s", (child[0],))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('parent_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
