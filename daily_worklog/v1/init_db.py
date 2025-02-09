from app import create_app, db
from app.models import Factory, Process, Equipment, Product, Template, CheckItem
import json

def init_db():
    app = create_app()
    with app.app_context():
        # 기존 데이터 삭제
        db.drop_all()
        db.create_all()

        # 공장 생성
        factory = Factory(name='CJ 식품공장', location='경기도 수원시')
        db.session.add(factory)
        db.session.flush()

        # 공정 생성
        processes = [
            Process(factory_id=factory.id, name='원료 입고', description='원료 입고 및 검수 공정'),
            Process(factory_id=factory.id, name='전처리', description='원료 전처리 공정'),
            Process(factory_id=factory.id, name='가공', description='주요 가공 공정'),
            Process(factory_id=factory.id, name='포장', description='제품 포장 공정')
        ]
        for process in processes:
            db.session.add(process)
        db.session.flush()

        # 설비 생성
        equipments = [
            Equipment(process_id=processes[0].id, name='입고 검수대', model_number='IK-001'),
            Equipment(process_id=processes[1].id, name='세척기', model_number='CL-001'),
            Equipment(process_id=processes[2].id, name='살균기', model_number='ST-001'),
            Equipment(process_id=processes[2].id, name='냉각기', model_number='CO-001'),
            Equipment(process_id=processes[3].id, name='포장기', model_number='PK-001')
        ]
        for equipment in equipments:
            db.session.add(equipment)

        # 제품 생성
        products = [
            Product(name='즉석밥', code='RIC-001', description='흰쌀밥'),
            Product(name='카레', code='CUR-001', description='즉석 카레'),
            Product(name='국물요리', code='SOU-001', description='즉석 국물요리')
        ]
        for product in products:
            db.session.add(product)

        # HACCP 기본 점검 항목
        check_items = {
            '전원': {'unit': 'V', 'min': 220, 'max': 240},
            '온도': {'unit': '°C', 'min': 0, 'max': 4},
            '습도': {'unit': '%', 'min': 30, 'max': 60},
            '압력': {'unit': 'Bar', 'min': 1, 'max': 5},
            'pH': {'unit': 'pH', 'min': 6.5, 'max': 7.5},
            '염소농도': {'unit': 'ppm', 'min': 0.4, 'max': 4.0}
        }

        for name, data in check_items.items():
            item = CheckItem(
                name=name,
                category='기본',
                unit=data['unit'],
                min_value=data['min'],
                max_value=data['max']
            )
            db.session.add(item)

        # 템플릿 생성
        template_data = [
            {
                'name': '입고 검수 점검',
                'process_id': processes[0].id,
                'equipment_id': equipments[0].id,
                'items': ['온도', 'pH']
            },
            {
                'name': '세척 공정 점검',
                'process_id': processes[1].id,
                'equipment_id': equipments[1].id,
                'items': ['전원', '압력', '염소농도']
            },
            {
                'name': '살균 공정 점검',
                'process_id': processes[2].id,
                'equipment_id': equipments[2].id,
                'items': ['전원', '온도', '압력']
            }
        ]

        for data in template_data:
            template_items = []
            for item_name in data['items']:
                item_data = check_items[item_name]
                template_items.append({
                    'name': item_name,
                    'unit': item_data['unit'],
                    'min': str(item_data['min']),
                    'max': str(item_data['max'])
                })

            template = Template(
                name=data['name'],
                factory_id=factory.id,
                process_id=data['process_id'],
                equipment_id=data['equipment_id'],
                check_items=json.dumps(template_items)
            )
            db.session.add(template)

        db.session.commit()
        print("초기 데이터가 성공적으로 생성되었습니다.")

if __name__ == '__main__':
    init_db() 