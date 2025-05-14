from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Item, User
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

with app.app_context():
    db.create_all()

# --- User Authentication ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect('/register')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully! Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            return redirect('/')
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect('/login')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.", 'danger')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

# --- Inventory Routes ---
@app.route('/')
@login_required
def index():
    items = Item.query.all()
    return render_template('index.html', items=items, mode='index')

@app.route('/add', methods=['POST'])
@login_required
def add():
    item = Item(
        item_name=request.form['item_name'],
        item_number=request.form['item_number'],
        quantity=int(request.form['quantity']),
        price=float(request.form['price']),
        user_id=session['user_id']
    )
    db.session.add(item)
    db.session.commit()
    flash('Item added successfully!', 'success')
    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        item.item_name = request.form['item_name']
        item.item_number = request.form['item_number']
        item.quantity = int(request.form['quantity'])
        item.price = float(request.form['price'])
        item.last_changed = datetime.now()
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect('/')
    return render_template('index.html', item=item, mode='edit')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!', 'danger')
    return redirect('/')

@app.route('/export')
@login_required
def export_csv():
    items = Item.query.all()
    with open('inventory_export.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date Added', 'Item Name', 'Item Number', 'Quantity', 'Price'])
        for item in items:
            writer.writerow([
                item.date_added.strftime('%Y-%m-%d'),
                item.item_name,
                item.item_number,
                item.quantity,
                item.price
            ])
    return redirect('/')

@app.route('/import', methods=['GET', 'POST'])
@login_required
def import_csv():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename.endswith('.csv'):
            csvfile = file.stream.read().decode('utf-8').splitlines()
            reader = csv.DictReader(csvfile)
            for row in reader:
                item = Item(
                    item_name=row['Item Name'],
                    item_number=row['Item Number'],
                    quantity=int(row['Quantity']),
                    price=float(row['Price']),
                    user_id=session['user_id']
                )
                db.session.add(item)
            db.session.commit()
            flash('Items imported successfully!', 'success')
        else:
            flash('Only CSV files are supported.', 'danger')
        return redirect('/')
    return render_template('index.html', mode='import')
if __name__ == '__main__':
    app.run(debug=True)
