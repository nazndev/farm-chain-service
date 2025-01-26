from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_restx import Api, Resource, fields
from db import db
from models import TraceabilityRecord, Contract
import asyncio
from py_eureka_client.eureka_client import EurekaClient
import uuid
import time
import requests
from functools import wraps

# Flask app initialization
app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)  # Initialize the database with the Flask app

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Swagger/RESTX API setup with Authorization
authorizations = {
    "BearerAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Enter your Bearer token in the format: Bearer <token>"
    }
}
api = Api(
    app,
    version="1.0",
    title="FarmChain Service API",
    description="API documentation for the FarmChain Service",
    security="BearerAuth",
    authorizations=authorizations,
)

# Eureka client configuration
eureka_client = EurekaClient(
    eureka_server="http://localhost:8761/",
    app_name="farm-chain-service",
    instance_port=5000,
    instance_ip="127.0.0.1"
)

# Start Eureka client to register the service
asyncio.run(eureka_client.start())

# Namespaces for organization
traceability_ns = api.namespace("traceability", description="Traceability Endpoints")
smart_contract_ns = api.namespace("smart-contract", description="Smart Contract Endpoints")

# Models for request/response validation
traceability_model = api.model('TraceabilityRecord', {
    'product_id': fields.String(required=True, description='Product ID'),
    'farmer_id': fields.String(required=True, description='Farmer ID'),
    'aggregation_center_id': fields.String(required=True, description='Aggregation Center ID')
})

smart_contract_model = api.model('SmartContract', {
    'buyer_id': fields.String(required=True, description='Buyer ID'),
    'seller_id': fields.String(required=True, description='Seller ID'),
    'product_id': fields.String(required=True, description='Product ID'),
    'agreed_price': fields.Float(required=True, description='Agreed Price'),
    'delivery_date': fields.String(required=True, description='Delivery Date')
})

# Auto-create tables (for development only)
with app.app_context():
    db.create_all()

# Auth Service configuration
AUTH_SERVICE_VALIDATE_URL = "http://localhost:8081/auth/public/validate"


# Middleware to validate token and extract permissions
def validate_token():
    token = request.headers.get("Authorization", None)
    if not token:
        return False, "Token is missing"

    try:
        # Validate the token by sending a request to the Auth Service
        response = requests.post(AUTH_SERVICE_VALIDATE_URL, headers={"Authorization": token})
        if response.status_code != 200:
            return False, "Invalid token"

        # Return token claims (including permissions)
        return True, response.json()  # Example payload: {"permissions": ["CREATE_RECORD", "UPDATE_RECORD"]}
    except Exception as e:
        return False, f"Token validation failed: {str(e)}"


def has_permission(required_permission):
    """Decorator to check if the user has the required permission"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            is_valid, user_or_error = validate_token()
            if not is_valid:
                api.abort(401, user_or_error)

            # Check if the user has the required permission
            user_permissions = user_or_error.get("permissions", [])
            if required_permission not in user_permissions:
                api.abort(403, "Access denied: insufficient permission")

            return f(*args, **kwargs)
        return wrapper
    return decorator


# Traceability Endpoints
@traceability_ns.route('/')
class TraceabilityResource(Resource):
    @traceability_ns.expect(traceability_model)
    @traceability_ns.response(201, "Traceability record created successfully")
    @api.doc(security="BearerAuth")
    @has_permission("CREATE_RECORD")
    def post(self):
        """Create a new traceability record"""
        print("Headers:", request.headers)  # Debug headers
        print("Payload:", request.json)     # Debug request payload
        data = request.json
        product_id = data.get('product_id')
        farmer_id = data.get('farmer_id')
        aggregation_center_id = data.get('aggregation_center_id')

        if not product_id or not farmer_id or not aggregation_center_id:
            api.abort(400, "Missing required fields")

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

        return {"traceability_hash": traceability_hash, "timestamp": timestamp}, 201

@traceability_ns.route('/<string:traceability_hash>')
class TraceabilityDetailResource(Resource):
    @traceability_ns.response(200, "Success")
    @traceability_ns.response(404, "Traceability record not found")
    @api.doc(security="BearerAuth")
    @has_permission("VIEW_RECORD")  # Permission required to view a traceability record
    def get(self, traceability_hash):
        """Retrieve a traceability record by hash"""
        record = TraceabilityRecord.query.filter_by(traceability_hash=traceability_hash).first()
        if not record:
            api.abort(404, "Traceability record not found")

        return {
            "product_id": record.product_id,
            "farmer_id": record.farmer_id,
            "aggregation_center_id": record.aggregation_center_id,
            "timestamp": record.timestamp
        }, 200

# Smart Contract Endpoints
@smart_contract_ns.route('/')
class SmartContractResource(Resource):
    @smart_contract_ns.expect(smart_contract_model)
    @smart_contract_ns.response(201, "Smart contract created successfully")
    @api.doc(security="BearerAuth")
    @has_permission("CREATE_CONTRACT")  # Permission required to create a smart contract
    def post(self):
        """Create a new smart contract"""
        data = request.json
        buyer_id = data.get('buyer_id')
        seller_id = data.get('seller_id')
        product_id = data.get('product_id')
        agreed_price = data.get('agreed_price')
        delivery_date = data.get('delivery_date')

        if not all([buyer_id, seller_id, product_id, agreed_price, delivery_date]):
            api.abort(400, "Missing required fields")

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

        return {"contract_id": contract_id, "status": "Pending"}, 201

@smart_contract_ns.route('/<string:contract_id>')
class SmartContractDetailResource(Resource):
    @smart_contract_ns.response(200, "Success")
    @smart_contract_ns.response(404, "Contract not found")
    @api.doc(security="BearerAuth")
    @has_permission("UPDATE_CONTRACT")  # Permission required to update a smart contract
    def patch(self, contract_id):
        """Update the status of a smart contract"""
        contract = Contract.query.filter_by(contract_id=contract_id).first()
        if not contract:
            api.abort(404, "Contract not found")

        data = request.json
        status = data.get('status')

        if status not in ["Pending", "Completed", "Cancelled"]:
            api.abort(400, "Invalid status")

        contract.status = status
        db.session.commit()
        return {"contract_id": contract_id, "status": status}, 200


@smart_contract_ns.route('/lock-payment')
class LockPaymentResource(Resource):
    @smart_contract_ns.expect(api.model('LockPayment', {
        'product_id': fields.String(required=True, description='Product ID'),
        'retailer_id': fields.String(required=True, description='Retailer ID'),
        'amount': fields.Float(required=True, description='Payment Amount'),
    }))
    @smart_contract_ns.response(201, "Payment locked successfully")
    @has_permission("LOCK_PAYMENT")
    def post(self):
        """Lock payment for a product using a smart contract"""
        data = request.json
        product_id = data.get('product_id')
        retailer_id = data.get('retailer_id')
        amount = data.get('amount')

        if not all([product_id, retailer_id, amount]):
            api.abort(400, "Missing required fields")

        # Simulate locking payment in smart contract
        contract_id = str(uuid.uuid4())
        return {"contract_id": contract_id, "status": "Payment Locked"}, 201


@smart_contract_ns.route('/release-payment')
class ReleasePaymentResource(Resource):
    @smart_contract_ns.expect(api.model('ReleasePayment', {
        'product_id': fields.String(required=True, description='Product ID'),
        'retailer_id': fields.String(required=True, description='Retailer ID'),
        'amount': fields.Float(required=True, description='Payment Amount'),
    }))
    @smart_contract_ns.response(201, "Payment released successfully")
    @has_permission("RELEASE_PAYMENT")
    def post(self):
        """Release payment for a product using a smart contract"""
        data = request.json
        product_id = data.get('product_id')
        retailer_id = data.get('retailer_id')
        amount = data.get('amount')

        if not all([product_id, retailer_id, amount]):
            api.abort(400, "Missing required fields")

        # Simulate releasing payment in smart contract
        return {"status": "Payment Released"}, 201



if __name__ == '__main__':
    app.run(port=5000)
