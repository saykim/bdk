from . import db
from datetime import datetime
import json

class Factory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Process(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    factory_id = db.Column(db.Integer, db.ForeignKey('factory.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    factory = db.relationship('Factory', backref=db.backref('processes', lazy=True))

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    model_number = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    process = db.relationship('Process', backref=db.backref('equipments', lazy=True))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    factory_id = db.Column(db.Integer, db.ForeignKey('factory.id'))
    process_id = db.Column(db.Integer, db.ForeignKey('process.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    check_items = db.Column(db.Text, nullable=False)  # JSON 형식으로 저장
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    factory = db.relationship('Factory', backref=db.backref('templates', lazy=True))
    process = db.relationship('Process', backref=db.backref('templates', lazy=True))
    equipment = db.relationship('Equipment', backref=db.backref('templates', lazy=True))
    product = db.relationship('Product', backref=db.backref('templates', lazy=True))

    def __repr__(self):
        return f'<Template {self.name}>'

class CheckItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 전원, 온도, 습도, 압력 등
    unit = db.Column(db.String(20))  # °C, %, Bar 등
    min_value = db.Column(db.Float)  # 최소 허용값
    max_value = db.Column(db.Float)  # 최대 허용값
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WorkLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.id'), nullable=False)
    inspector = db.Column(db.String(100), nullable=False)  # 점검자
    shift = db.Column(db.String(20))  # 근무조
    data = db.Column(db.Text, nullable=False)  # JSON 형식으로 저장
    status = db.Column(db.String(20), default='대기중')  # 대기중, 승인됨, 거부됨
    notes = db.Column(db.Text)  # 특이사항
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = db.relationship('Template', backref=db.backref('work_logs', lazy=True))

    def __repr__(self):
        return f'<WorkLog {self.id}>'

    @property
    def has_critical_values(self):
        """허용 범위를 벗어난 항목이 있는지 확인"""
        check_items = CheckItem.query.all()
        check_items_dict = {item.name: item for item in check_items}
        data = json.loads(self.data)
        
        for key, value in data.items():
            if key in check_items_dict:
                item = check_items_dict[key]
                try:
                    value = float(value)
                    if (item.min_value is not None and value < item.min_value) or \
                       (item.max_value is not None and value > item.max_value):
                        return True
                except (ValueError, TypeError):
                    continue
        return False 