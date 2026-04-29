from flask import Blueprint, request, jsonify, session, current_app
import os
import qrcode
from datetime import datetime
from app.models import Medicine, Batch
from app.routes.auth import role_required
from app import db

bp = Blueprint('medicine', __name__)

@bp.route('/medicine/create', methods=['POST'])
@role_required('manufacturer')
def create_medicine():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Invalid input', 'message': 'Medicine name is required'}), 400

    new_medicine = Medicine(
        name=data.get('name'),
        manufacturer_id=session.get('user_id')
    )
    
    db.session.add(new_medicine)
    db.session.commit()

    return jsonify({
        'message': 'Medicine created successfully',
        'medicine': {
            'id': new_medicine.id,
            'name': new_medicine.name,
            'manufacturer_id': new_medicine.manufacturer_id
        }
    }), 201

@bp.route('/medicines', methods=['GET'])
def get_all_medicines():
    medicines = Medicine.query.all()
    result = []
    for m in medicines:
        result.append({
            'id': m.id,
            'name': m.name,
            'manufacturer_id': m.manufacturer_id
        })
    return jsonify({'medicines': result}), 200

@bp.route('/batch/create', methods=['POST'])
@role_required('manufacturer')
def create_batch():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input', 'message': 'No JSON data provided'}), 400

    medicine_id = data.get('medicine_id')
    batch_number = data.get('batch_number')
    mfg_date_str = data.get('mfg_date')
    expiry_date_str = data.get('expiry_date')

    if not all([medicine_id, batch_number, mfg_date_str, expiry_date_str]):
        return jsonify({'error': 'Missing fields', 'message': 'medicine_id, batch_number, mfg_date, and expiry_date are required'}), 400

    # check duplicate batch_number
    existing_batch = Batch.query.filter_by(batch_number=batch_number).first()
    if existing_batch:
        return jsonify({'error': 'Duplicate batch', 'message': 'A batch with this number already exists'}), 409

    # parse dates
    try:
        mfg_date = datetime.strptime(mfg_date_str, '%Y-%m-%d')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format', 'message': 'Dates must be in YYYY-MM-DD format'}), 400

    if expiry_date <= mfg_date:
        return jsonify({'error': 'Invalid dates', 'message': 'Expiry date must be after manufacturing date'}), 400

    # Verify medicine belongs to this manufacturer
    medicine = Medicine.query.get(medicine_id)
    if not medicine:
        return jsonify({'error': 'Not found', 'message': 'Medicine not found'}), 404
        
    if medicine.manufacturer_id != session.get('user_id'):
        return jsonify({'error': 'Forbidden', 'message': 'You do not own this medicine'}), 403

    # Ensure qrcodes directory exists
    qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    # Generate QR Code
    qr_data = f"Batch: {batch_number}\nMedicine ID: {medicine_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code
    filename = f"qr_{batch_number}.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)

    qr_code_url_path = f"/static/qrcodes/{filename}"

    new_batch = Batch(
        batch_number=batch_number,
        medicine_id=medicine_id,
        mfg_date=mfg_date,
        expiry_date=expiry_date,
        qr_code_path=qr_code_url_path
    )
    
    db.session.add(new_batch)
    db.session.commit()

    return jsonify({
        'message': 'Batch created successfully',
        'batch': {
            'id': new_batch.id,
            'batch_number': new_batch.batch_number,
            'medicine_id': new_batch.medicine_id,
            'mfg_date': new_batch.mfg_date.strftime('%Y-%m-%d'),
            'expiry_date': new_batch.expiry_date.strftime('%Y-%m-%d'),
            'qr_code_path': new_batch.qr_code_path
        }
    }), 201

@bp.route('/batches', methods=['GET'])
def get_all_batches():
    batches = Batch.query.all()
    result = []
    for b in batches:
        result.append({
            'id': b.id,
            'batch_number': b.batch_number,
            'medicine_id': b.medicine_id,
            'mfg_date': b.mfg_date.strftime('%Y-%m-%d'),
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d')
        })
    return jsonify({'batches': result}), 200

@bp.route('/batches/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    b = Batch.query.get(batch_id)
    if not b:
        return jsonify({'error': 'Not found', 'message': 'Batch not found'}), 404
        
    return jsonify({
        'batch': {
            'id': b.id,
            'batch_number': b.batch_number,
            'medicine_id': b.medicine_id,
            'mfg_date': b.mfg_date.strftime('%Y-%m-%d'),
            'expiry_date': b.expiry_date.strftime('%Y-%m-%d')
        }
    }), 200
