from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecret"  # Needed for flash messages
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tms_lite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    truck_number = db.Column(db.String(50), nullable=False)
    shipments = db.relationship('Shipment', backref='driver', lazy=True, cascade="all, delete-orphan")

class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    boxes = db.relationship('Box', backref='shipment', lazy=True, cascade="all, delete-orphan")
    history = db.relationship('ShipmentHistory', backref='shipment', lazy=True, cascade="all, delete-orphan")

class Box(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)

class ShipmentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200), nullable=False)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- HTML Template ---
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TMS Lite 🚛</title>
<style>
*{box-sizing:border-box;transition:0.2s ease-in-out;}
body{font-family:'Segoe UI', Roboto, sans-serif;background:#f5f7fa;margin:0;padding:0;color:#222;}
header{background:#0d6efd;color:white;padding:1.5rem 2rem;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);}
main{max-width:1000px;margin:40px auto;background:white;border-radius:16px;box-shadow:0 8px 20px rgba(0,0,0,0.08);padding:30px;}
h1,h2{margin-top:0;}
form{margin-bottom:30px;background:#f8f9fc;border:1px solid #e3e6f0;padding:20px;border-radius:12px;}
input,select{width:100%;padding:10px;margin:8px 0;border:1px solid #ccc;border-radius:8px;font-size:15px;}
input:focus,select:focus{border-color:#0d6efd;outline:none;box-shadow:0 0 5px rgba(13,110,253,0.3);}
button{padding:10px 20px;background:#0d6efd;color:white;border:none;border-radius:8px;font-size:15px;cursor:pointer;}
button:hover{background:#0b5ed7;transform:translateY(-1px);box-shadow:0 3px 8px rgba(13,110,253,0.3);}
.delete-btn{background:#dc3545;margin-left:5px;}
.delete-btn:hover{background:#bb2d3b;box-shadow:0 3px 8px rgba(220,53,69,0.3);}
table{width:100%;border-collapse:collapse;margin-top:25px;}
th,td{padding:12px 10px;border-bottom:1px solid #eee;text-align:left;}
th{background:#f1f3f9;}
tr:hover{background:#f8fafc;}
footer{text-align:center;padding:20px;color:#777;}
.box-list{font-size:14px;margin-top:5px;}
.flash{background:#ffc107;color:#000;padding:10px;border-radius:8px;margin-bottom:20px;}
@media(max-width:600px){main{padding:20px;}table{font-size:14px;}}
</style>
</head>
<body>
<header>
<h1>🚚 TMS Lite</h1>
<p>Simple Transport Management System</p>
</header>
<main>
{% with messages = get_flashed_messages() %}
    {% if messages %}
        {% for msg in messages %}
            <div class="flash">{{ msg }}</div>
        {% endfor %}
    {% endif %}
{% endwith %}

<h2>Add Driver</h2>
<form action="/add_driver" method="post">
<input type="text" name="name" placeholder="Driver Name" required>
<input type="text" name="truck_number" placeholder="Truck Number" required>
<button type="submit">➕ Add Driver</button>
</form>

<h2>Drivers</h2>
<table>
<tr><th>ID</th><th>Name</th><th>Truck Number</th><th>Actions</th></tr>
{% for d in drivers %}
<tr>
<td>{{ d.id }}</td>
<td>{{ d.name }}</td>
<td>{{ d.truck_number }}</td>
<td>
<form action="/delete_driver/{{ d.id }}" method="post" style="display:inline;">
<button type="submit" class="delete-btn">🗑 Delete</button>
</form>
</td>
</tr>
{% endfor %}
</table>

<h2>Create Shipment</h2>
<form action="/add_shipment" method="post">
<input type="text" name="customer_name" placeholder="Customer Name" required>
<input type="text" name="origin" placeholder="Origin" required>
<input type="text" name="destination" placeholder="Destination" required>
<select name="driver_id">
<option value="">-- Assign Driver (optional) --</option>
{% for driver in drivers %}
<option value="{{ driver.id }}">{{ driver.name }} - {{ driver.truck_number }}</option>
{% endfor %}
</select>
<button type="submit">📦 Create Shipment</button>
</form>

<h2>Shipments</h2>
<table>
<tr><th>ID</th><th>Customer</th><th>Origin</th><th>Destination</th>
<th>Status</th><th>Driver</th><th>Boxes</th><th>Actions</th></tr>
{% for s in shipments %}
<tr>
<td>{{ s.id }}</td>
<td>{{ s.customer_name }}</td>
<td>{{ s.origin }}</td>
<td>{{ s.destination }}</td>
<td>
<form action="/update_status/{{ s.id }}" method="post">
<select name="status" onchange="this.form.submit()">
{% for st in ['Pending','In Transit','Delivered','Cancelled'] %}
<option value="{{ st }}" {% if s.status == st %}selected{% endif %}>{{ st }}</option>
{% endfor %}
</select>
</form>
</td>
<td>{{ s.driver.name if s.driver else 'Unassigned' }}</td>
<td>
<ul class="box-list">
{% for b in s.boxes %}
<li>{{ b.code }}</li>
{% endfor %}
</ul>
<form action="/add_box/{{ s.id }}" method="post">
<input type="text" name="code" placeholder="Scan/Add Box" required>
<button type="submit">➕</button>
</form>
</td>
<td>
<form action="/delete_shipment/{{ s.id }}" method="post">
<button type="submit" class="delete-btn">🗑 Delete</button>
</form>
</td>
</tr>
<tr>
<td colspan="8">
<strong>History:</strong>
<ul>
{% for h in s.history %}
<li>{{ h.action }}</li>
{% endfor %}
</ul>
</td>
</tr>
{% endfor %}
</table>
</main>
<footer>
<p>© 2025 TMS Lite — built with Flask</p>
</footer>
</body>
</html>
"""

# --- Routes ---
@app.route('/')
def index():
    drivers = Driver.query.all()
    shipments = Shipment.query.all()
    return render_template_string(HTML, drivers=drivers, shipments=shipments)

@app.route('/add_driver', methods=['POST'])
def add_driver():
    db.session.add(Driver(name=request.form['name'], truck_number=request.form['truck_number']))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_driver/<int:driver_id>', methods=['POST'])
def delete_driver(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_shipment', methods=['POST'])
def add_shipment():
    driver_id = request.form.get('driver_id') or None
    if driver_id == "":
        driver_id = None
    shipment = Shipment(
        customer_name=request.form['customer_name'],
        origin=request.form['origin'],
        destination=request.form['destination'],
        driver_id=driver_id
    )
    db.session.add(shipment)
    db.session.commit()
    # Add initial history
    history = ShipmentHistory(action=f"Shipment created for {shipment.customer_name}", shipment=shipment)
    db.session.add(history)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_shipment/<int:shipment_id>', methods=['POST'])
def delete_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    db.session.delete(shipment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update_status/<int:shipment_id>', methods=['POST'])
def update_status(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    new_status = request.form['status']
    shipment.status = new_status
    db.session.add(ShipmentHistory(action=f"Status changed to '{new_status}'", shipment=shipment))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_box/<int:shipment_id>', methods=['POST'])
def add_box(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    code = request.form['code']
    # Check duplicate
    if Box.query.filter_by(shipment_id=shipment.id, code=code).first():
        flash(f"Box '{code}' already scanned for this shipment!")
        return redirect(url_for('index'))
    box = Box(code=code, shipment=shipment)
    db.session.add(box)
    db.session.add(ShipmentHistory(action=f"Box '{code}' added", shipment=shipment))
    db.session.commit()
    return redirect(url_for('index'))

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
