from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import os
from models import ProductionOrder, Session, init_db
from utils import generate_pdf, generate_excel, ensure_upload_folder

app = Flask(__name__)

# 업로드 폴더 생성
ensure_upload_folder()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/orders', methods=['GET'])
def get_orders():
    session = Session()
    orders = session.query(ProductionOrder).all()
    result = [order.to_dict() for order in orders]
    session.close()
    return jsonify(result)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    session = Session()
    
    new_order = ProductionOrder(
        factory=data['factory'],
        product=data['product'],
        order_no=data['order_no'],
        quantity=float(data['quantity']),
        start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M'),
        end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M'),
        status=data['status']
    )
    
    session.add(new_order)
    session.commit()
    result = new_order.to_dict()
    session.close()
    
    return jsonify({"message": "생산오더가 생성되었습니다.", "order": result})

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    session = Session()
    
    order = session.query(ProductionOrder).get(order_id)
    if not order:
        session.close()
        return jsonify({"error": "생산오더를 찾을 수 없습니다."}), 404
    
    if 'start_time' in data:
        order.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M')
    if 'end_time' in data:
        order.end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M')
    if 'status' in data:
        order.status = data['status']
    
    session.commit()
    result = order.to_dict()
    session.close()
    
    return jsonify({"message": "생산오더가 업데이트되었습니다.", "order": result})

@app.route('/api/export/pdf')
def export_pdf():
    session = Session()
    orders = session.query(ProductionOrder).all()
    
    output_path = os.path.join('static', 'exports', f'production_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
    generate_pdf(orders, output_path)
    
    session.close()
    return send_file(output_path, as_attachment=True)

@app.route('/api/export/excel')
def export_excel():
    session = Session()
    orders = session.query(ProductionOrder).all()
    
    output_path = os.path.join('static', 'exports', f'production_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    generate_excel(orders, output_path)
    
    session.close()
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 