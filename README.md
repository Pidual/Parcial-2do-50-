# Sistema de Reserva de Citas Médicas

## Visión General
Este sistema permite gestionar reservas de citas médicas de forma asíncrona, utilizando RabbitMQ para procesar las solicitudes y notificar los cambios de estado.

## Componentes de Mensajería

### Exchanges
Un **Exchange** es el punto de entrada de mensajes en RabbitMQ, actúa como un distribuidor que recibe mensajes de los productores y los enruta a las colas apropiadas.

En nuestro sistema:
- Utilizamos un exchange tipo **fanout** llamado `booking_notifications`
- Este exchange distribuye las notificaciones de cambios de estado (confirmado/rechazado) a todos los servicios suscritos
- No filtra mensajes, sino que los envía a todas las colas vinculadas

<code># En worker.py
def publish_notification(booking):
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    # Define el exchange booking_notifications
    channel.exchange_declare(exchange='booking_notifications', exchange_type='fanout')
    message = f"Cita para {booking.paciente} - {booking.estado}"
    channel.basic_publish(exchange='booking_notifications', routing_key='', body=message)
    connection.close() </code>

### Producers (Productores)
Los **Productores** son las partes del sistema que envían mensajes a RabbitMQ para ser procesados.

En nuestra aplicación:
- La API REST actúa como productor principal cuando recibe solicitudes de citas
- Envía las solicitudes al sistema de colas para procesamiento asíncrono
- También el worker se convierte en productor cuando publica notificaciones

### Queues (Colas)
Las **Colas** almacenan los mensajes hasta que son procesados por los consumidores.

En este sistema:
- La cola principal `booking_queue` almacena las solicitudes de citas pendientes
- Es durable (persiste si el servidor se reinicia)
- Implementa un mecanismo de distribución equitativa de trabajo entre consumidores
- Utiliza acknowledgments para garantizar que los mensajes se procesen correctamente

### Consumers (Consumidores)
Los **Consumidores** reciben y procesan los mensajes de las colas.

En nuestra aplicación:
- El servicio worker es el consumidor principal, procesando las solicitudes de la cola
- Simula el proceso de confirmación de citas con un retraso artificial
- Actualiza el estado de las citas en la base de datos
- Publica notificaciones cuando cambia el estado de una cita

## Flujo de Trabajo
1. El cliente envía solicitud de cita a la API REST
2. La API guarda la solicitud como "pendiente" y la envía a la cola
3. El worker consume el mensaje, simula procesamiento y actualiza el estado
4. El worker publica una notificación al exchange
5. Servicios suscritos reciben la notificación y actúan en consecuencia

## Decisiones Arquitectónicas
- **Tolerancia a fallos**: Si un worker cae, otros pueden seguir procesando mensajes
- **Escalabilidad horizontal**: Se pueden añadir más workers para manejar mayor carga
- **Asincronía**: El cliente no necesita esperar a que se complete el procesamiento
- **Desacoplamiento**: Los componentes del sistema pueden evolucionar independientemente
