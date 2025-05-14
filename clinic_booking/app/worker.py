import pika, time, random, json
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Booking  # Keep absolute import for worker.py

# Initialize Flask app for database context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def publish_notification(booking):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    # Define el exchange booking_notifications
    channel.exchange_declare(exchange='booking_notifications', exchange_type='fanout')
    message = f"Cita para {booking.paciente} - {booking.estado}"
    channel.basic_publish(exchange='booking_notifications', routing_key='', body=message)
    connection.close()

def booking_worker():
    def callback(ch, method, properties, body):
        try:
            with app.app_context():
                data = json.loads(body)
                booking_id = data['id']
                print(f"Processing booking {booking_id}")
                
                # Simulate processing delay
                delay = random.randint(2, 5)
                time.sleep(delay)
                
                booking = Booking.query.get(booking_id)
                if not booking:
                    print(f"Booking {booking_id} not found")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Simulate occasional failure
                if random.random() < 0.1:
                    print(f"Simulated failure for booking {booking_id}")
                    booking.estado = 'rejected'
                else:
                    print(f"Confirming booking {booking_id}")
                    booking.estado = 'confirmed'
                
                db.session.commit()
                publish_notification(booking)
                print(f"Processed booking {booking_id}: {booking.estado}")
        except Exception as e:
            print(f"Error processing message: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Wait for RabbitMQ to be ready
    retries = 5
    while retries > 0:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='rabbitmq',
                heartbeat=600,
                blocked_connection_timeout=300
            ))
            break
        except pika.exceptions.AMQPConnectionError:
            retries -= 1
            print("RabbitMQ not ready, retrying...")
            time.sleep(5)

    if retries <= 0:
        print("Failed to connect to RabbitMQ")
        return

    channel = connection.channel()
    channel.queue_declare(queue='booking_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='booking_queue', on_message_callback=callback)
    
    print("Worker active and waiting for tasks...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    # Wait for database to be ready
    time.sleep(10)
    with app.app_context():
        db.create_all()
    booking_worker()