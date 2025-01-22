from flask import Flask, request, jsonify
from flask_migrate import Migrate

from db import db
from models import TraceabilityRecord, Contract
import asyncio
from py_eureka_client.eureka_client import EurekaClient
import uuid
import time

app = Flask(__name__)
app.config.from_pyfile('config.py')  # Load configuration from config.py

db.init_app(app)  # Initialize the database with the Flask app

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Auto-create tables (for development only)
with app.app_context():
    db.create_all()

# Eureka client configuration
eureka_client = EurekaClient(
    eureka_server="http://localhost:8761/",
    app_name="farm-chain-service",
    instance_port=5000,
    instance_ip="127.0.0.1"
)

# Start Eureka client to register the service
asyncio.run(eureka_client.start())

@app.route('/traceability', methods=['POST'])
def create_traceability_record():
    data = request.json
    product_id = data.get('product_id')
    farmer_id = data.get('farmer_id')
    aggregation_center_id = data.get('aggregation_center_id')

    if not product_id or not farmer_id or not aggregation_center_id:
        return jsonify({"error": "Missing required fields"}), 400

    traceability_hash = str(uuid.uuid4())  # Simulate hash generation
    timestamp = time.time()

    # Save to database
    record = TraceabilityRecord(
        traceability_hash=traceability_hash,
        product_id=product_id,
        farmer_id=farmer_id,
        aggregation_center_id=aggregation_center_id,
        timestamp=timestamp
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "traceability_hash": traceability_hash,
        "timestamp": timestamp
    }), 201


@app.route('/smart-contract', methods=['POST'])
def create_smart_contract():
    data = request.json
    buyer_id = data.get('buyer_id')
    seller_id = data.get('seller_id')
    product_id = data.get('product_id')
    agreed_price = data.get('agreed_price')
    delivery_date = data.get('delivery_date')

    if not all([buyer_id, seller_id, product_id, agreed_price, delivery_date]):
        return jsonify({"error": "Missing required fields"}), 400

    contract_id = str(uuid.uuid4())

    # Save to database
    contract = Contract(
        contract_id=contract_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        product_id=product_id,
        agreed_price=agreed_price,
        delivery_date=delivery_date
    )
    db.session.add(contract)
    db.session.commit()

    return jsonify({"contract_id": contract_id, "status": "Pending"}), 201


@app.route('/traceability/<traceability_hash>', methods=['GET'])
def get_traceability_record(traceability_hash):
    record = TraceabilityRecord.query.filter_by(traceability_hash=traceability_hash).first()
    if not record:
        return jsonify({"error": "Traceability record not found"}), 404

    return jsonify({
        "product_id": record.product_id,
        "farmer_id": record.farmer_id,
        "aggregation_center_id": record.aggregation_center_id,
        "timestamp": record.timestamp
    }), 200


@app.route('/smart-contract/<contract_id>', methods=['PATCH'])
def update_contract_status(contract_id):
    contract = Contract.query.filter_by(contract_id=contract_id).first()
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    data = request.json
    status = data.get('status')

    if status not in ["Pending", "Completed", "Cancelled"]:
        return jsonify({"error": "Invalid status"}), 400

    contract.status = status
    db.session.commit()
    return jsonify({"contract_id": contract_id, "status": status}), 200


if __name__ == '__main__':
    app.run(port=5000)