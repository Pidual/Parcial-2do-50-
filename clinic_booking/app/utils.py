import pika
from .models import Booking  # Changed back to relative import

def publish_notification(booking):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.exchange_declare(exchange='booking_notifications', exchange_type='fanout')
    message = f"Cita para {booking.paciente} - {booking.estado}"
    channel.basic_publish(exchange='booking_notifications', routing_key='', body=message)
    connection.close()