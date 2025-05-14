# routes.py
from flask import Blueprint, request, jsonify
from .models import Booking, db
from .tasks import enqueue_booking

bp = Blueprint('routes', __name__)



# /BOOK para crear reserva con datos de paciente y franja horaria.
@bp.route('/book', methods=['POST'])
def book():
    data = request.json
    booking = Booking(paciente=data['paciente'], franja=data['franja'], estado='pending')
    db.session.add(booking)
    db.session.commit()
    enqueue_booking(booking.id)  # Enviar a la cola
    return jsonify({'booking_id': booking.id})

# ara consultar estado (pending, confirmed, rejected)
@bp.route('/booking/<int:id>', methods=['GET'])
def check_status(id):
    booking = Booking.query.get_or_404(id)
    return jsonify({'estado': booking.estado})
