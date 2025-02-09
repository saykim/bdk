from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class ProductionOrder(Base):
    __tablename__ = 'production_orders'

    id = Column(Integer, primary_key=True)
    factory = Column(String(100), nullable=False)  # 공장
    product = Column(String(100), nullable=False)  # 제품
    order_no = Column(String(50), nullable=False)  # 생산오더 번호
    quantity = Column(Float, nullable=False)       # 수량
    start_time = Column(DateTime, nullable=False)  # 시작 시간
    end_time = Column(DateTime, nullable=False)    # 종료 시간
    status = Column(String(20), nullable=False)    # 상태 (계획/생산/완료/변경)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'factory': self.factory,
            'product': self.product,
            'order_no': self.order_no,
            'quantity': self.quantity,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M'),
            'status': self.status
        }

# 데이터베이스 연결 설정
engine = create_engine('sqlite:///production.db')
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine) 