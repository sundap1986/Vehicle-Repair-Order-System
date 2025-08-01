from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = '1e6ccffe1d49eff841fd0c401551b457'

# Database setup
def init_db():
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    
    # Create repair orders table
    c.execute('''CREATE TABLE IF NOT EXISTS repair_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE,
        reg_number TEXT,
        vin_number TEXT,
        kms INTEGER,
        vehicle_in_date TEXT,
        vehicle_in_time TEXT,
        make TEXT,
        model TEXT,
        driver_name TEXT,
        phone_number TEXT,
        vehicle_came_from_site TEXT,
        site_incharge_name TEXT,
        driver_permanent TEXT,
        road_test_along TEXT,
        service_type TEXT,
        under_warranty TEXT,
        repair_estimation_cost REAL,
        expected_delivery_date TEXT,
        expected_delivery_time TEXT,
        allotted_technician TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'Open'
    )''')
    
    # Create spare parts table
    c.execute('''CREATE TABLE IF NOT EXISTS spare_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        part_description TEXT,
        part_number TEXT,
        make TEXT,
        unit_cost REAL,
        quantity INTEGER,
        amount REAL,
        FOREIGN KEY (order_id) REFERENCES repair_orders (id)
    )''')
    
    # Create labor details table
    c.execute('''CREATE TABLE IF NOT EXISTS labor_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        description TEXT,
        labor_charges REAL,
        outside_labor REAL,
        amount REAL,
        FOREIGN KEY (order_id) REFERENCES repair_orders (id)
    )''')
    
    # Create vehicle checks table
    c.execute('''CREATE TABLE IF NOT EXISTS vehicle_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        oil_level TEXT,
        housing_oil_level TEXT,
        clutch_oil_level TEXT,
        battery_lights_check TEXT,
        general_checks_done TEXT,
        stepney_condition TEXT,
        steering_oil_level TEXT,
        other_oil_leakages TEXT,
        tyres_stepney_condition TEXT,
        FOREIGN KEY (order_id) REFERENCES repair_orders (id)
    )''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    c.execute('SELECT * FROM repair_orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    return render_template('index.html', orders=orders)

@app.route('/create_order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        # Generate order number
        order_number = f"RO-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        conn = sqlite3.connect('repair_orders.db')
        c = conn.cursor()
        
        # Insert repair order
        c.execute('''INSERT INTO repair_orders 
                    (order_number, reg_number, vin_number, kms, vehicle_in_date, vehicle_in_time,
                     make, model, driver_name, phone_number, vehicle_came_from_site, site_incharge_name,
                     driver_permanent, road_test_along, service_type, under_warranty, repair_estimation_cost,
                     expected_delivery_date, expected_delivery_time, allotted_technician, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (order_number, request.form['reg_number'], request.form['vin_number'],
                  request.form.get('kms', 0), request.form['vehicle_in_date'], request.form['vehicle_in_time'],
                  request.form['make'], request.form['model'], request.form['driver_name'],
                  request.form['phone_number'], request.form['vehicle_came_from_site'],
                  request.form['site_incharge_name'], request.form['driver_permanent'],
                  request.form['road_test_along'], request.form['service_type'],
                  request.form['under_warranty'], request.form.get('repair_estimation_cost', 0),
                  request.form['expected_delivery_date'], request.form['expected_delivery_time'],
                  request.form['allotted_technician'], datetime.now().isoformat()))
        
        order_id = c.lastrowid
        
        # Insert vehicle checks
        c.execute('''INSERT INTO vehicle_checks 
                    (order_id, oil_level, housing_oil_level, clutch_oil_level, battery_lights_check,
                     general_checks_done, stepney_condition, steering_oil_level, other_oil_leakages,
                     tyres_stepney_condition)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (order_id, request.form.get('oil_level'), request.form.get('housing_oil_level'),
                  request.form.get('clutch_oil_level'), request.form.get('battery_lights_check'),
                  request.form.get('general_checks_done'), request.form.get('stepney_condition'),
                  request.form.get('steering_oil_level'), request.form.get('other_oil_leakages'),
                  request.form.get('tyres_stepney_condition')))
        
        conn.commit()
        conn.close()
        
        flash(f'Repair order {order_number} created successfully!', 'success')
        return redirect(url_for('view_order', order_id=order_id))
    
    return render_template('create_order.html')

@app.route('/order/<int:order_id>')
def view_order(order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    
    # Get order details
    c.execute('SELECT * FROM repair_orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    
    if not order:
        flash('Order not found!', 'error')
        return redirect(url_for('index'))
    
    # Get spare parts
    c.execute('SELECT * FROM spare_parts WHERE order_id = ?', (order_id,))
    spare_parts = c.fetchall()
    
    # Get labor details
    c.execute('SELECT * FROM labor_details WHERE order_id = ?', (order_id,))
    labor_details = c.fetchall()
    
    # Get vehicle checks
    c.execute('SELECT * FROM vehicle_checks WHERE order_id = ?', (order_id,))
    vehicle_checks = c.fetchone()
    
    conn.close()
    
    return render_template('view_order.html', order=order, spare_parts=spare_parts,
                         labor_details=labor_details, vehicle_checks=vehicle_checks)

@app.route('/add_spare_part/<int:order_id>', methods=['POST'])
def add_spare_part(order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    
    part_description = request.form['part_description']
    part_number = request.form['part_number']
    make = request.form['make']
    unit_cost = float(request.form['unit_cost'])
    quantity = int(request.form['quantity'])
    amount = unit_cost * quantity
    
    c.execute('''INSERT INTO spare_parts 
                (order_id, part_description, part_number, make, unit_cost, quantity, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
             (order_id, part_description, part_number, make, unit_cost, quantity, amount))
    
    conn.commit()
    conn.close()
    
    flash('Spare part added successfully!', 'success')
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/add_labor/<int:order_id>', methods=['POST'])
def add_labor(order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    
    description = request.form['description']
    labor_charges = float(request.form.get('labor_charges', 0))
    outside_labor = float(request.form.get('outside_labor', 0))
    amount = labor_charges + outside_labor
    
    c.execute('''INSERT INTO labor_details 
                (order_id, description, labor_charges, outside_labor, amount)
                VALUES (?, ?, ?, ?, ?)''',
             (order_id, description, labor_charges, outside_labor, amount))
    
    conn.commit()
    conn.close()
    
    flash('Labor detail added successfully!', 'success')
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form['status']
    
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    c.execute('UPDATE repair_orders SET status = ? WHERE id = ?', (new_status, order_id))
    conn.commit()
    conn.close()
    
    flash(f'Order status updated to {new_status}!', 'success')
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/delete_spare_part/<int:part_id>/<int:order_id>')
def delete_spare_part(part_id, order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    c.execute('DELETE FROM spare_parts WHERE id = ?', (part_id,))
    conn.commit()
    conn.close()
    
    flash('Spare part deleted successfully!', 'success')
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/delete_labor/<int:labor_id>/<int:order_id>')
def delete_labor(labor_id, order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    c.execute('DELETE FROM labor_details WHERE id = ?', (labor_id,))
    conn.commit()
    conn.close()
    
    flash('Labor detail deleted successfully!', 'success')
    return redirect(url_for('view_order', order_id=order_id))

@app.route('/api/order_totals/<int:order_id>')
def get_order_totals(order_id):
    conn = sqlite3.connect('repair_orders.db')
    c = conn.cursor()
    
    # Get spare parts total
    c.execute('SELECT SUM(amount) FROM spare_parts WHERE order_id = ?', (order_id,))
    parts_total = c.fetchone()[0] or 0
    
    # Get labor total
    c.execute('SELECT SUM(amount) FROM labor_details WHERE order_id = ?', (order_id,))
    labor_total = c.fetchone()[0] or 0
    
    conn.close()
    
    grand_total = parts_total + labor_total
    
    return jsonify({
        'parts_total': parts_total,
        'labor_total': labor_total,
        'grand_total': grand_total
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True)