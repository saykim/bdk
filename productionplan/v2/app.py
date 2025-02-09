import sqlite3
from flask import Flask, request, jsonify, render_template, g
from datetime import datetime, timedelta

app = Flask(__name__)
DATABASE = 'production.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        db.close()

def is_valid_time(time_str):
    try:
        hh, mm = time_str.split(':')
        hh = int(hh)
        mm = int(mm)
        return 0 <= hh < 24 and 0 <= mm <60
    except:
        return False

def calculate_end_datetime(start_date, start_time, duration_hours):
    start_str = f"{start_date} {start_time}"
    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(hours=duration_hours)
    return end_dt.strftime("%Y-%m-%d %H:%M")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_plan', methods=['POST'])
def add_plan():
    try:
        data = request.get_json()
        
        # 필수 필드 검증
        required_fields = ['date', 'start_time', 'duration', 'line', 'product_id', 'product_name', 'bom', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Missing field: {field}'}), 400

        # 시작 시간과 종료 시간 계산
        start_datetime = datetime.strptime(f"{data['date']} {data['start_time']}", "%Y-%m-%d %H:%M")
        duration_hours = float(data['duration'])
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        conn = get_db()
        cur = conn.cursor()
        
        # 계획 추가
        cur.execute('''
            INSERT INTO plans (date, start_time, duration, end_time, line, product_id, product_name, bom, quantity, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['date'],
            data['start_time'],
            duration_hours,
            end_datetime.strftime("%Y-%m-%d %H:%M"),
            data['line'],
            data['product_id'],
            data['product_name'],
            data['bom'],
            data['quantity'],
            data.get('notes', '')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print('Error:', str(e))  # 서버 로그에 에러 출력
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/update_plan/<int:plan_id>', methods=['POST'])
def update_plan(plan_id):
    data = request.json
    date = data.get('date')
    start_time = data.get('startTime')
    duration = data.get('duration')
    line = data.get('line')
    product_name = data.get('productName')
    bom = data.get('bom')
    notes = data.get('notes','')
    quantity = data.get('quantity','0')

    if not date:
        return jsonify({"error":"일자 필요"}),400
    if not start_time or not is_valid_time(start_time):
        return jsonify({"error":"시작시간 오류"}),400
    try:
        d_val = float(duration)
        if d_val<=0 or d_val>24:
            return jsonify({"error":"생산시간 범위 오류"}),400
    except:
        return jsonify({"error":"생산시간 숫자"}),400
    try:
        l_val = int(line)
        if l_val<1 or l_val>15:
            return jsonify({"error":"라인 범위"}),400
    except:
        return jsonify({"error":"라인 숫자"}),400
    if not product_name:
        return jsonify({"error":"제품명 필요"}),400

    end_str = calculate_end_datetime(date, start_time, float(duration))

    db = get_db()
    db.execute('UPDATE plans SET date=?,start_time=?,duration=?,end_time=?,line=?,product_name=?,bom=?,notes=?,quantity=? WHERE id=?',
               (date, start_time, float(duration), end_str, l_val, product_name, bom, notes, quantity, plan_id))
    db.commit()
    return get_all_plans()

@app.route('/delete_plan/<int:plan_id>', methods=['DELETE'])
def delete_plan(plan_id):
    db = get_db()
    db.execute('DELETE FROM plans WHERE id=?',(plan_id,))
    db.commit()
    return get_all_plans()

@app.route('/done_plan/<int:plan_id>', methods=['PATCH'])
def done_plan(plan_id):
    db = get_db()
    db.execute('UPDATE plans SET done=1 WHERE id=?',(plan_id,))
    db.commit()
    return get_all_plans()

@app.route('/undone_plan/<int:plan_id>', methods=['PATCH'])
def undone_plan(plan_id):
    db = get_db()
    db.execute('UPDATE plans SET done=0 WHERE id=?',(plan_id,))
    db.commit()
    return get_all_plans()

@app.route('/plans', methods=['GET'])
def get_all_plans():
    db = get_db()
    rows = db.execute('SELECT * FROM plans').fetchall()
    plans = [dict(row) for row in rows]
    return jsonify({"plans": plans})

# 기준정보 페이지
@app.route('/products')
def products_page():
    return render_template('products.html')

@app.route('/get_products', methods=['GET'])
def get_products():
    db = get_db()
    rows = db.execute('SELECT * FROM products').fetchall()
    result = [dict(r) for r in rows]
    return jsonify({"products": result})

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.json
    product_name = data.get('product_name')
    bom = data.get('bom')
    if not product_name:
        return jsonify({"error":"제품명 필요"}),400
    
    db = get_db()
    db.execute('INSERT INTO products(product_name,bom) VALUES(?,?)',(product_name,bom))
    db.commit()
    return get_products()

@app.route('/update_product/<int:prod_id>', methods=['POST'])
def update_product(prod_id):
    data = request.json
    product_name = data.get('product_name')
    bom = data.get('bom')
    if not product_name:
        return jsonify({"error":"제품명 필요"}),400

    db = get_db()
    db.execute('UPDATE products SET product_name=?,bom=? WHERE id=?',(product_name,bom,prod_id))
    db.commit()
    return get_products()

@app.route('/delete_product/<int:prod_id>', methods=['DELETE'])
def delete_product(prod_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id=?',(prod_id,))
    db.commit()
    return get_products()

@app.route('/summary', methods=['GET'])
def summary():
    db = get_db()
    rows = db.execute('SELECT date, product_name, bom, SUM(quantity) as total_qty FROM plans WHERE done=1 GROUP BY date, product_name, bom').fetchall()
    result = [dict(r) for r in rows]
    return jsonify({"summary": result})

if __name__ == '__main__':
    init_db()  # DB 초기화
    app.run(debug=True)