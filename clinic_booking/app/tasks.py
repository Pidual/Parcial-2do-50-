# tasks.py
import pika, time, random, json
from .models import db, Booking  # Changed back to relative import
from threading import Thread
from .utils import publish_notification  # Changed back to relative import

def enqueue_booking(booking_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='booking_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='booking_queue',
        body=json.dumps({'id': booking_id}),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

def booking_worker():
    def callback(ch, method, properties, body):
        data = json.loads(body)
        booking_id = data['id']
        delay = random.randint(2, 5)
        time.sleep(delay)
        try:
            booking = Booking.query.get(booking_id)
            if random.random() < 0.1:  # Simula fallo
                raise Exception("Error al confirmar")
            booking.estado = 'confirmed'
        except:
            booking.estado = 'rejected'
        db.session.commit()
        publish_notification(booking)  # Notificar a través del exchange
        ch.basic_ack(delivery_tag=method.delivery_tag)

    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    channel.queue_declare(queue='booking_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='booking_queue', on_message_callback=callback)
    print("Worker activo esperando tareas...")
    channel.start_consuming()
