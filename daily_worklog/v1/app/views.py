from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .models import db, Template, WorkLog, Factory, Process, Equipment, Product, CheckItem
import json
from datetime import datetime, timedelta
from pytz import timezone
import pytz

main_bp = Blueprint('main', __name__)

@main_bp.context_processor
def utility_processor():
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        if value is None:
            return ""
        seoul_tz = pytz.timezone('Asia/Seoul')
        if value.tzinfo is None:
            value = pytz.utc.localize(value)
        return value.astimezone(seoul_tz).strftime(format)
    
    def get_now():
        seoul_tz = pytz.timezone('Asia/Seoul')
        return datetime.now(seoul_tz)
    
    return dict(
        format_datetime=format_datetime,
        now=get_now,
        current_year=get_now().year
    )

@main_bp.route('/api/processes/<int:factory_id>')
def get_processes(factory_id):
    processes = Process.query.filter_by(factory_id=factory_id).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in processes])

@main_bp.route('/api/equipments/<int:process_id>')
def get_equipments(process_id):
    equipments = Equipment.query.filter_by(process_id=process_id).all()
    return jsonify([{'id': e.id, 'name': e.name} for e in equipments])

@main_bp.route('/')
def index():
    # 검색 파라미터 가져오기
    template_name = request.args.get('template_name', '').strip()
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    status = request.args.get('status', '')
    factory_id = request.args.get('factory_id', type=int)
    process_id = request.args.get('process_id', type=int)
    equipment_id = request.args.get('equipment_id', type=int)

    # 기본 쿼리 생성
    query = WorkLog.query.join(Template)

    # 템플릿 이름으로 검색
    if template_name:
        query = query.filter(Template.name.ilike(f'%{template_name}%'))

    # 날짜 범위로 검색
    if start_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(WorkLog.created_at >= start_datetime)
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(WorkLog.created_at < end_datetime)

    # 상태로 검색
    if status:
        query = query.filter(WorkLog.status == status)

    # 공장/공정/설비로 검색
    if factory_id:
        query = query.filter(Template.factory_id == factory_id)
    if process_id:
        query = query.filter(Template.process_id == process_id)
    if equipment_id:
        query = query.filter(Template.equipment_id == equipment_id)

    # 결과 정렬
    work_logs = query.order_by(WorkLog.created_at.desc()).all()
    
    # 공장 목록 가져오기 (검색 필터용)
    factories = Factory.query.order_by(Factory.name).all()
    
    # 대시보드 데이터 준비
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_logs = WorkLog.query.filter(
        db.func.date(WorkLog.created_at) == today
    ).all()
    
    yesterday_logs = WorkLog.query.filter(
        db.func.date(WorkLog.created_at) == yesterday
    ).all()
    
    pending_logs = WorkLog.query.filter(
        WorkLog.status == '대기중'
    ).all()
    
    critical_logs = WorkLog.query.filter(
        WorkLog.has_critical_values == True
    ).all()
    
    completed_logs = WorkLog.query.filter(
        db.func.date(WorkLog.created_at) == today,
        WorkLog.status.in_(['승인됨', '거부됨'])
    ).all()
    
    total_templates = Template.query.all()

    return render_template('index.html', 
                         work_logs=work_logs,
                         template_name=template_name,
                         start_date=start_date,
                         end_date=end_date,
                         status=status,
                         factories=factories,
                         factory_id=factory_id,
                         process_id=process_id,
                         equipment_id=equipment_id,
                         today_logs=today_logs,
                         yesterday_logs=yesterday_logs,
                         pending_logs=pending_logs,
                         critical_logs=critical_logs,
                         completed_logs=completed_logs,
                         total_templates=total_templates)

@main_bp.route('/templates')
def templates():
    templates = Template.query.order_by(Template.created_at.desc()).all()
    return render_template('templates.html', templates=templates)

@main_bp.route('/template/create', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        name = request.form.get('name')
        factory_id = request.form.get('factory_id')
        process_id = request.form.get('process_id')
        equipment_id = request.form.get('equipment_id')
        product_id = request.form.get('product_id')
        check_items = request.form.get('check_items')
        
        if not name or not check_items:
            flash('필수 항목을 모두 입력해주세요.', 'error')
            return redirect(url_for('main.create_template'))
        
        # 체크 항목 생성 또는 업데이트
        items_data = json.loads(check_items)
        for item_data in items_data:
            check_item = CheckItem.query.filter_by(name=item_data['name']).first()
            if not check_item:
                check_item = CheckItem(
                    name=item_data['name'],
                    category='custom',  # 또는 적절한 카테고리
                    unit=item_data['unit']
                )
                if item_data['min']:
                    check_item.min_value = float(item_data['min'])
                if item_data['max']:
                    check_item.max_value = float(item_data['max'])
                db.session.add(check_item)
        
        template = Template(
            name=name,
            factory_id=factory_id,
            process_id=process_id,
            equipment_id=equipment_id,
            product_id=product_id,
            check_items=check_items
        )
        db.session.add(template)
        db.session.commit()
        
        flash('템플릿이 생성되었습니다.', 'success')
        return redirect(url_for('main.templates'))
    
    factories = Factory.query.order_by(Factory.name).all()
    products = Product.query.order_by(Product.name).all()
    return render_template('create_template.html', 
                         factories=factories,
                         products=products)

@main_bp.route('/worklog/create', methods=['GET', 'POST'])
def create_worklog():
    if request.method == 'POST':
        template_id = request.form.get('template_id')
        inspector = request.form.get('inspector')
        shift = request.form.get('shift')
        notes = request.form.get('notes', '')
        
        if not all([template_id, inspector, shift]):
            flash('필수 항목을 모두 입력해주세요.', 'error')
            return redirect(url_for('main.create_worklog'))
        
        template = Template.query.get_or_404(template_id)
        check_items = json.loads(template.check_items)
        data = {}
        has_critical = False
        
        # 점검 항목 데이터 수집
        for item in check_items:
            value = request.form.get(item['name'])
            status = request.form.get(f"{item['name']}_status")
            
            if not value:
                flash(f'{item["name"]} 항목의 값을 입력해주세요.', 'error')
                return redirect(url_for('main.create_worklog'))
            
            try:
                float_value = float(value)
                if (item.get('min') and float_value < float(item['min'])) or \
                   (item.get('max') and float_value > float(item['max'])):
                    has_critical = True
            except ValueError:
                pass
            
            data[item['name']] = {
                'value': value,
                'unit': item.get('unit', ''),
                'status': status,
                'min': item.get('min'),
                'max': item.get('max')
            }
        
        worklog = WorkLog(
            template_id=template_id,
            inspector=inspector,
            shift=shift,
            data=json.dumps(data),
            notes=notes,
            status='대기중' if has_critical else '승인됨'
        )
        db.session.add(worklog)
        db.session.commit()
        
        if has_critical:
            flash('허용 범위를 벗어난 항목이 있어 승인 대기 상태로 저장되었습니다.', 'warning')
        else:
            flash('작업 로그가 생성되었습니다.', 'success')
        return redirect(url_for('main.index'))
    
    templates = Template.query.order_by(Template.name).all()
    return render_template('create_worklog.html', templates=templates)

@main_bp.route('/worklog/<int:id>/edit', methods=['GET', 'POST'])
def edit_worklog(id):
    worklog = WorkLog.query.get_or_404(id)
    
    if request.method == 'POST':
        inspector = request.form.get('inspector')
        shift = request.form.get('shift')
        notes = request.form.get('notes', '')
        status = request.form.get('status')
        
        if not all([inspector, shift]):
            flash('필수 항목을 모두 입력해주세요.', 'error')
            return redirect(url_for('main.edit_worklog', id=id))
        
        check_items = json.loads(worklog.template.check_items)
        data = {}
        has_critical = False
        
        # 점검 항목 데이터 수집
        for item in check_items:
            value = request.form.get(item['name'])
            item_status = request.form.get(f"{item['name']}_status")
            
            if not value:
                flash(f'{item["name"]} 항목의 값을 입력해주세요.', 'error')
                return redirect(url_for('main.edit_worklog', id=id))
            
            try:
                float_value = float(value)
                if (item.get('min') and float_value < float(item['min'])) or \
                   (item.get('max') and float_value > float(item['max'])):
                    has_critical = True
            except ValueError:
                pass
            
            data[item['name']] = {
                'value': value,
                'unit': item.get('unit', ''),
                'status': item_status,
                'min': item.get('min'),
                'max': item.get('max')
            }
        
        worklog.inspector = inspector
        worklog.shift = shift
        worklog.notes = notes
        worklog.data = json.dumps(data)
        
        # 상태가 명시적으로 변경되지 않은 경우에만 자동 설정
        if not status:
            worklog.status = '대기중' if has_critical else '승인됨'
        else:
            worklog.status = status
            
        db.session.commit()
        
        if has_critical and not status:
            flash('허용 범위를 벗어난 항목이 있어 승인 대기 상태로 저장되었습니다.', 'warning')
        else:
            flash('작업 로그가 수정되었습니다.', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('edit_worklog.html', worklog=worklog)

@main_bp.route('/worklog/<int:id>/delete', methods=['POST'])
def delete_worklog(id):
    worklog = WorkLog.query.get_or_404(id)
    db.session.delete(worklog)
    db.session.commit()
    
    flash('작업 로그가 삭제되었습니다.', 'success')
    return redirect(url_for('main.index')) 