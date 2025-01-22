from db import db

class TraceabilityRecord(db.Model):
    __tablename__ = 'traceability_records'
    id = db.Column(db.Integer, primary_key=True)
    traceability_hash = db.Column(db.String(100), unique=True, nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    farmer_id = db.Column(db.String(100), nullable=False)
    aggregation_center_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)

class Contract(db.Model):
    __tablename__ = 'contracts'
    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(db.String(100), unique=True, nullable=False)
    buyer_id = db.Column(db.String(100), nullable=False)
    seller_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    agreed_price = db.Column(db.Float, nullable=False)
    delivery_date = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="Pending")
