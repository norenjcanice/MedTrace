from flask import Blueprint, request, jsonify, session
from app.models import Batch, SupplyLog
from app.routes.auth import role_required
from app import db

bp = Blueprint('supply', __name__)

@bp.route('/update-supply', methods=['POST'])
@role_required('distributor', 'pharmacy')
def update_supply():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input', 'message': 'No JSON data provided'}), 400

    batch_id = data.get('batch_id')
    to_role = data.get('to_role')
    location = data.get('location')

    if not all([batch_id, to_role, location]):
        return jsonify({'error': 'Missing fields', 'message': 'batch_id, to_role, and location are required'}), 400

    batch = Batch.query.get(batch_id)
    if not batch:
        return jsonify({'error': 'Not found', 'message': 'Batch not found'}), 404

    logs = SupplyLog.query.filter_by(batch_id=batch_id).order_by(SupplyLog.timestamp.asc()).all()
    
    current_stage = 'manufacturer'
    if logs:
        current_stage = logs[-1].to_role

    if to_role == 'distributor':
        if current_stage == 'distributor':
            return jsonify({'error': 'Duplicate entry', 'message': 'Batch has already been received by a distributor'}), 409
        if current_stage != 'manufacturer':
            return jsonify({'error': 'Invalid flow', 'message': f'Cannot move to distributor from {current_stage}'}), 400
        from_role = 'manufacturer'

    elif to_role == 'pharmacy':
        if current_stage == 'manufacturer':
            return jsonify({'error': 'Skipped step', 'message': 'Batch must go to a distributor before pharmacy'}), 400
        if current_stage == 'pharmacy':
            return jsonify({'error': 'Duplicate entry', 'message': 'Batch has already been received by a pharmacy'}), 409
        if current_stage != 'distributor':
            return jsonify({'error': 'Invalid flow', 'message': f'Cannot move to pharmacy from {current_stage}'}), 400
        from_role = 'distributor'
        
    else:
        return jsonify({'error': 'Invalid to_role', 'message': 'to_role must be distributor or pharmacy'}), 400

    new_log = SupplyLog(
        batch_id=batch_id,
        from_role=from_role,
        to_role=to_role,
        location=location
    )
    
    db.session.add(new_log)
    db.session.commit()

    return jsonify({
        'message': 'Supply chain movement updated successfully',
        'current_stage': to_role,
        'log': {
            'id': new_log.id,
            'batch_id': new_log.batch_id,
            'from_role': new_log.from_role,
            'to_role': new_log.to_role,
            'location': new_log.location,
            'timestamp': new_log.timestamp.isoformat() if new_log.timestamp else None
        }
    }), 201
