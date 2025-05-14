from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente = db.Column(db.String(100), nullable=False)
    franja = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.paciente}>'