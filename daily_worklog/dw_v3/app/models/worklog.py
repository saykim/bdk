from app import db
from datetime import datetime

class WorkLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    order_number = db.Column(db.String(50), nullable=False)
    work_start_time = db.Column(db.DateTime, nullable=False)
    work_end_time = db.Column(db.DateTime, nullable=False)
    quantity_produced = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    quality_check = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', backref=db.backref('worklogs', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_name': self.product_name,
            'order_number': self.order_number,
            'work_start_time': self.work_start_time.isoformat(),
            'work_end_time': self.work_end_time.isoformat(),
            'quantity_produced': self.quantity_produced,
            'unit': self.unit,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'quality_check': self.quality_check,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 