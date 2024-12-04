from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong key for production

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='mobileshopee',
            user='root',
            password=''
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

# Route to check if the database connection works
@app.route('/check_connection', methods=['GET'])
def check_connection():
    conn = get_db_connection()
    if conn:
        conn.close()  # Close connection after checking
        return jsonify({"message": "Connection successful"})
    else:
        return jsonify({"message": "Connection failed"}), 500

# Login required decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access this page", category="danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Ensure the original function name is preserved
    return wrapper

# Superadmin page
@app.route('/super_home')
def super_home():
    if session.get('role') != 'superadmin':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('super_home.html')

# Admin page
@app.route('/admin_home')
def admin_home():
    if session.get('role') not in ['admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_home.html')

# User home page
@app.route('/user_home')
def user_home():
    if 'user_id' not in session:
        flash('Please log in to continue.', 'danger')
        return redirect(url_for('login'))
    return render_template('user_home.html')

# Cart page
@app.route('/cart')
def cart():
    return render_template('cart.html')

# Homepage route
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Account page route
@app.route('/account_page')
def account_page():
    return render_template('account_page.html')

@app.route('/seller_approve')
def seller_approve():
    return render_template('seller_approve.html')

@app.route('/seller_dashboard')
@login_required
def seller_dashboard():
    # Ensure seller status is updated in session if user is approved
    session['seller_status'] = 'approved'  # This is just for illustration; you may already have this set during registration
    return render_template('seller_dashboard.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clears all session data (logs the user out)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Admin home user management
@app.route('/admin_home_user', methods=['GET'])
@login_required
def admin_home_user():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password, role FROM users")
        rows = cursor.fetchall()
        return render_template('admin_home_user.html', users=rows)

    except Error as e:
        flash("An error occurred while fetching users", "danger")
        print("Error:", e)
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()

# Admin home sellers management
@app.route('/admin_home_sellers', methods=['GET'])
@login_required
def admin_home_sellers():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sellers WHERE status = 'approved'")
        rows = cursor.fetchall()
        return render_template('admin_home_sellers.html', sellers=rows)

    except Error as e:
        flash("An error occurred while fetching approved sellers", "danger")
        print("Error:", e)
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()

# Admin home seller registration
@app.route('/admin_home_reg', methods=['GET'])
@login_required
def admin_home_reg():
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('home'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sellers")
        rows = cursor.fetchall()
        return render_template('admin_home_reg.html', sellers=rows)

    except Error as e:
        flash("An error occurred while fetching seller applications", "danger")
        print("Error:", e)
        return redirect(url_for('home'))

    finally:
        if conn:
            conn.close()


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE email = %s AND password = %s"
                cursor.execute(query, (email, password))
                user = cursor.fetchone()

                if user:
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    flash('Login successful!', 'success')

                    if user['role'] == 'superadmin':
                        return redirect(url_for('super_home'))
                    elif user['role'] == 'admin':
                        return redirect(url_for('admin_home'))
                    else:
                        return redirect(url_for('user_home'))
                else:
                    flash('Invalid email or password.', 'danger')
            except Error as e:
                flash('An error occurred while processing your request.', 'danger')
                print(f"Error: {e}")
            finally:
                conn.close()
        else:
            flash('Unable to connect to the database.', 'danger')
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email format.', 'danger')
            return redirect(url_for('signup'))

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                check_query = "SELECT * FROM users WHERE email = %s"
                cursor.execute(check_query, (email,))
                if cursor.fetchone():
                    flash('Email is already registered.', 'warning')
                    return redirect(url_for('signup'))

                insert_query = "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (email, password, 'user'))
                conn.commit()
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            except Error as e:
                flash('An error occurred while processing your request.', 'danger')
                print(f"Error: {e}")
            finally:
                conn.close()
        else:
            flash('Unable to connect to the database.', 'danger')
    return render_template('signup.html')

# Seller registration route
@app.route('/seller_registration', methods=['GET', 'POST'])
@login_required
def seller_registration():
    conn = get_db_connection()
    if not conn:
        flash("Failed to connect to the database", "danger")
        return redirect(url_for('user_home'))

    user_id = session['user_id']
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM sellers WHERE user_id = %s", (user_id,))
        existing_seller = cursor.fetchone()

        if existing_seller:
            # Set the seller status in session
            session['seller_status'] = existing_seller['status']

            if existing_seller['status'] == 'Approved':
                if not session.get('seen_approval'):
                    session['seen_approval'] = True
                    return render_template('seller_approve.html')
                return redirect(url_for('seller_dashboard'))
            elif existing_seller['status'] == 'declined':
                flash("Your application was declined. You can reapply.", "warning")
            else:
                flash("Your application is still pending.", "info")
                return render_template('reg_after_sub.html')

        if request.method == 'POST':
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            email = request.form.get('email')
            phone_number = request.form.get('phoneNumber')
            address = request.form.get('address')
            postal_code = request.form.get('postalCode')
            city = request.form.get('city')

            cursor.execute("INSERT INTO sellers (user_id, first_name, last_name, email, phone_number, address, postal_code, city, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')",
                           (user_id, first_name, last_name, email, phone_number, address, postal_code, city))
            conn.commit()

            flash('Seller registration submitted. Please wait for approval.', 'success')
            return redirect(url_for('user_home'))

    except Error as e:
        flash("An error occurred during seller registration.", "danger")
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

    return render_template('seller_registration.html')



# Admin approve seller
@app.route('/approve_seller/<int:seller_id>', methods=['POST'])
@login_required
def approve_seller(seller_id):
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection error", category="danger")
        return redirect(url_for('admin_home_reg'))

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sellers SET status = 'approved' WHERE id = %s", (seller_id,))
        conn.commit()
        flash("Seller approved successfully!", category="success")

    except Error as e:
        flash("Failed to approve seller", category="danger")
        print(f"Error approving seller: {e}")
        conn.rollback()

    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin_home_reg'))


# Admin decline seller
@app.route('/decline_seller/<int:seller_id>', methods=['POST'])
@login_required
def decline_seller(seller_id):
    if session.get('role') != 'admin':
        flash("Access restricted", category="danger")
        return redirect(url_for('home'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection error", category="danger")
        return redirect(url_for('admin_home_reg'))

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sellers SET status = 'declined' WHERE id = %s", (seller_id,))
        conn.commit()
        flash("Seller declined successfully!", category="success")

    except Error as e:
        flash("Failed to decline seller", category="danger")
        print(f"Error declining seller: {e}")
        conn.rollback()

    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin_home_reg'))



if __name__ == '__main__':
    app.run(debug=True)
