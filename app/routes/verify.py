from flask import Blueprint, jsonify
from datetime import datetime
from app.models import Batch, SupplyLog, Medicine, User

bp = Blueprint('verify', __name__)

@bp.route('/verify/<batch_number>', methods=['GET'])
def verify_batch(batch_number):
    batch = Batch.query.filter_by(batch_number=batch_number).first()
    
    if not batch:
        return jsonify({
            "status": "Fake",
            "batch_number": batch_number,
            "medicine_name": "Unknown",
            "manufacturer": "Unknown",
            "supply_chain": []
        }), 404

    medicine = Medicine.query.get(batch.medicine_id)
    manufacturer = User.query.get(medicine.manufacturer_id)

    logs = SupplyLog.query.filter_by(batch_id=batch.id).order_by(SupplyLog.timestamp.asc()).all()
    
    supply_chain = []
    for log in logs:
        supply_chain.append({
            "from_role": log.from_role,
            "to_role": log.to_role,
            "location": log.location,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })

    # Base response data
    response_data = {
        "batch_number": batch.batch_number,
        "medicine_name": medicine.name if medicine else "Unknown",
        "manufacturer": manufacturer.name if manufacturer else "Unknown",
        "supply_chain": supply_chain
    }

    # 1. Check Expiry
    if batch.expiry_date < datetime.utcnow():
        response_data["status"] = "Expired"
        return jsonify(response_data), 200

    # 2. Check Supply Chain flow and anomalies
    # Expected valid flow: Manufacturer -> Distributor -> Pharmacy
    expected_transitions = [
        ('manufacturer', 'distributor'),
        ('distributor', 'pharmacy')
    ]
    
    actual_transitions = [(log.from_role, log.to_role) for log in logs]
    
    if actual_transitions != expected_transitions:
        response_data["status"] = "Suspicious"
        return jsonify(response_data), 200

    # If all valid
    response_data["status"] = "Genuine"
    return jsonify(response_data), 200
