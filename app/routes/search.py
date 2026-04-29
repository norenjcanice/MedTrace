from flask import Blueprint, request, jsonify
from app.models import Medicine, Batch, SupplyLog
from sqlalchemy import func

bp = Blueprint('search', __name__)

@bp.route('/search-medicine', methods=['GET'])
def search_medicine():
    medicine_name = request.args.get('name')
    if not medicine_name:
        return jsonify({'error': 'Missing parameter', 'message': 'Please provide a medicine name'}), 400

    # 1. Fetch medicine (case-insensitive)
    medicine = Medicine.query.filter(func.lower(Medicine.name) == func.lower(medicine_name)).first()
    
    if not medicine:
        return jsonify({
            'message': 'Medicine not found',
            'medicine': medicine_name,
            'available_at': []
        }), 404

    # 2. Find batches of that medicine
    batches = Batch.query.filter_by(medicine_id=medicine.id).all()
    
    if not batches:
        return jsonify({
            'message': 'No batches available for this medicine',
            'medicine': medicine.name,
            'available_at': []
        }), 200

    available_at = []
    
    # 3. Check supply logs for batches that reached pharmacy
    for b in batches:
        # Get the latest supply log that moved the batch to a pharmacy
        log = SupplyLog.query.filter_by(batch_id=b.id, to_role='pharmacy').order_by(SupplyLog.timestamp.desc()).first()
        
        if log:
            # We don't have explicit Pharmacy name stored in SupplyLog, just the location
            available_at.append({
                "pharmacy": "Registered Pharmacy", # Placeholder since we only track 'location' in SupplyLog
                "location": log.location or "Unknown Location",
                "batch_number": b.batch_number
            })

    if not available_at:
        return jsonify({
            'message': 'No pharmacies currently have this medicine in stock',
            'medicine': medicine.name,
            'available_at': []
        }), 200

    return jsonify({
        "medicine": medicine.name,
        "available_at": available_at
    }), 200
