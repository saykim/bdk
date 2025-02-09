from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.worklog import WorkLog
from app import db
from datetime import datetime

bp = Blueprint('worklog', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('worklog/index.html')

@bp.route('/api/worklogs', methods=['GET'])
@login_required
def get_worklogs():
    worklogs = WorkLog.query.filter_by(user_id=current_user.id).order_by(WorkLog.created_at.desc()).all()
    return jsonify([worklog.to_dict() for worklog in worklogs])

@bp.route('/api/worklogs', methods=['POST'])
@login_required
def create_worklog():
    try:
        data = request.json
        
        # 시간 문자열을 datetime 객체로 변환
        work_start_time = datetime.fromisoformat(data['work_start_time'])
        work_end_time = datetime.fromisoformat(data['work_end_time'])
        
        worklog = WorkLog(
            user_id=current_user.id,
            product_name=data['product_name'],
            order_number=data['order_number'],
            work_start_time=work_start_time,
            work_end_time=work_end_time,
            quantity_produced=float(data['quantity_produced']),
            unit=data['unit'],
            temperature=float(data.get('temperature', 0)),
            humidity=float(data.get('humidity', 0)),
            quality_check=data.get('quality_check', False),
            notes=data.get('notes', '')
        )
        
        db.session.add(worklog)
        db.session.commit()
        
        return jsonify({'message': '작업 일지가 성공적으로 저장되었습니다.', 'worklog': worklog.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/worklogs/<int:id>', methods=['PUT'])
@login_required
def update_worklog(id):
    try:
        worklog = WorkLog.query.get_or_404(id)
        
        if worklog.user_id != current_user.id:
            return jsonify({'error': '권한이 없습니다.'}), 403
            
        data = request.json
        
        # 시간 문자열을 datetime 객체로 변환
        work_start_time = datetime.fromisoformat(data['work_start_time'])
        work_end_time = datetime.fromisoformat(data['work_end_time'])
        
        worklog.product_name = data['product_name']
        worklog.order_number = data['order_number']
        worklog.work_start_time = work_start_time
        worklog.work_end_time = work_end_time
        worklog.quantity_produced = float(data['quantity_produced'])
        worklog.unit = data['unit']
        worklog.temperature = float(data.get('temperature', 0))
        worklog.humidity = float(data.get('humidity', 0))
        worklog.quality_check = data.get('quality_check', False)
        worklog.notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({'message': '작업 일지가 성공적으로 수정되었습니다.', 'worklog': worklog.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/api/worklogs/<int:id>', methods=['DELETE'])
@login_required
def delete_worklog(id):
    try:
        worklog = WorkLog.query.get_or_404(id)
        
        if worklog.user_id != current_user.id:
            return jsonify({'error': '권한이 없습니다.'}), 403
            
        db.session.delete(worklog)
        db.session.commit()
        
        return jsonify({'message': '작업 일지가 성공적으로 삭제되었습니다.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 