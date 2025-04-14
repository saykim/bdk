# -*- coding: utf-8 -*-
# 필수 라이브러리 설치 안내
# conda activate web310
# pip install streamlit simpy pandas plotly

try:
    import streamlit as st
    import simpy
    import random
    import statistics
    import pandas as pd
    import time
    from datetime import datetime
    import plotly.express as px
    import plotly.graph_objects as go
    import json
    import os
except ImportError as e:
    import sys
    print(f"필수 라이브러리 ImportError: {e}")
    try:
        import streamlit as st
        st.warning(f"필수 라이브러리 ImportError: {e}.\n'conda activate web310' 후 'pip install streamlit simpy pandas plotly'를 실행하세요.")
    except:
        pass
    sys.exit(1)

class Process:
    def __init__(self, name, min_time, max_time, capacity, is_quality_check=False):
        self.name = name
        self.min_time = min_time
        self.max_time = max_time
        self.capacity = capacity
        self.is_quality_check = is_quality_check

class Product:
    def __init__(self, name, processes):
        self.name = name
        self.processes = processes

class EquipmentMonitor:
    def __init__(self, name):
        self.name = name
        self.total_wait_time = 0
        self.total_process_time = 0
        self.request_count = 0
        self.completed_count = 0
        self.failed_count = 0
        self.start_times = {}  # 요청 시작 시간 저장
        self.queue_length_history = []

class FoodFactory:
    def __init__(self, env, product_type):
        self.env = env
        self.product_type = product_type
        self.equipment = {}
        self.equipment_monitors = {}
        self.processing_times = []
        self.process_logs = []
        self.failed_products = []
        self.progress = 0  # 진행 상황 추적을 위한 변수 추가
        self.total_products = 0  # 총 제품 수 추적
        
        # 각 공정별 설비 생성
        for process in product_type.processes:
            self.equipment[process.name] = simpy.Resource(env, capacity=process.capacity)
            self.equipment_monitors[process.name] = EquipmentMonitor(process.name)

    def process_step(self, product_id, process):
        monitor = self.equipment_monitors[process.name]
        request_time = self.env.now
        monitor.start_times[product_id] = request_time
        
        with self.equipment[process.name].request() as req:
            yield req
            
            # 대기 시간 계산
            wait_time = self.env.now - request_time
            monitor.total_wait_time += wait_time
            monitor.request_count += 1
            
            # 처리 시간
            processing_time = random.uniform(process.min_time, process.max_time)
            yield self.env.timeout(processing_time)
            
            monitor.total_process_time += processing_time
            monitor.completed_count += 1
            
            # 품질 검사 로직
            passed = True
            if process.is_quality_check:
                passed = random.random() > 0.1  # 10% 불량률
                if not passed:
                    monitor.failed_count += 1
            
            log = {
                'timestamp': self.env.now,
                'product_id': product_id,
                'process': process.name,
                'wait_time': wait_time,
                'process_time': processing_time,
                'total_time': wait_time + processing_time,
                'passed': passed if process.is_quality_check else None
            }
            self.process_logs.append(log)
            
            # 큐 길이 기록
            monitor.queue_length_history.append({
                'time': self.env.now,
                'queue_length': len(self.equipment[process.name].queue)
            })
            
            return passed

def product_line(env, product_id, factory):
    start_time = env.now
    failed = False
    
    for process in factory.product_type.processes:
        passed = yield from factory.process_step(product_id, process)
        if process.is_quality_check and not passed:
            failed = True
            factory.failed_products.append(product_id)
            break
    
    if not failed:
        total_time = env.now - start_time
        factory.processing_times.append(total_time)

def product_generator(env, factory, num_products):
    factory.total_products = num_products  # 총 제품 수 설정
    for i in range(num_products):
        yield env.timeout(random.uniform(2, 5))
        factory.progress = (i + 1) / num_products * 100  # 진행 상황 업데이트
        env.process(product_line(env, i, factory))

def save_product_types(product_types_dict):
    # 제품 타입을 JSON 형식으로 변환
    serialized_products = {}
    for name, product in product_types_dict.items():
        serialized_products[name] = {
            "name": product.name,
            "processes": [
                {
                    "name": p.name,
                    "min_time": p.min_time,
                    "max_time": p.max_time,
                    "capacity": p.capacity,
                    "is_quality_check": p.is_quality_check
                }
                for p in product.processes
            ]
        }
    
    # 디렉토리 생성 로직 추가
    os.makedirs('simpy', exist_ok=True)
    
    with open('simpy/product_types.json', 'w', encoding='utf-8') as f:
        json.dump(serialized_products, f, ensure_ascii=False, indent=2)

def load_product_types():
    try:
        with open('simpy/product_types.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            product_types = {}
            for name, product_data in data.items():
                processes = [
                    Process(
                        p["name"],
                        p["min_time"],
                        p["max_time"],
                        p["capacity"],
                        p.get("is_quality_check", False)  # 기본값 False로 설정
                    )
                    for p in product_data["processes"]
                ]
                product_types[name] = Product(name, processes)
            return product_types
    except FileNotFoundError:
        # 기본 제품 타입 반환
        return get_default_product_types()

def get_default_product_types():
    # 즉석식품 공정
    instant_food_processes = [
        Process("해동", 10, 15, 2),
        Process("전처리", 8, 12, 3),
        Process("계량", 3, 5, 2),
        Process("배합", 5, 8, 2),
        Process("투입", 2, 4, 2),
        Process("가공/조리", 15, 25, 4),
        Process("엑스레이검사", 2, 3, 1, is_quality_check=True),
        Process("금속검출", 1, 2, 1, is_quality_check=True),
        Process("내부포장", 5, 8, 2),
        Process("일차인기", 3, 5, 2),
        Process("외부포장", 5, 8, 2),
        Process("패킹", 3, 5, 3)
    ]
    
    # 음료 공정
    beverage_processes = [
        Process("원료계량", 5, 8, 2),
        Process("배합", 10, 15, 3),
        Process("살균", 20, 30, 2),
        Process("충진", 5, 8, 4),
        Process("검사", 2, 3, 1, is_quality_check=True),
        Process("라벨링", 3, 5, 2),
        Process("박스포장", 4, 6, 3)
    ]
    
    return {
        "즉석식품": Product("즉석식품", instant_food_processes),
        "음료": Product("음료", beverage_processes)
    }

# 공정 리스트 깊은 복사 함수
def copy_process_list(process_list):
    return [Process(p.name, p.min_time, p.max_time, p.capacity, p.is_quality_check) for p in process_list]

# 위젯 키 생성 함수
def make_widget_key(base, idx, ts):
    return f"{base}_{idx}_{ts}"

# 공정 추가 위치 옵션 생성 함수
def get_position_options(processes):
    return ["맨 위", "맨 아래"] + [f"공정 {i+1} 다음" for i in range(len(processes))]

# 컬럼명 한글화 함수
def rename_columns(df, col_map):
    return df.rename(columns=col_map)

def edit_product_type(product_types, selected_product):
    st.subheader(f"{selected_product} 공정 설정")
    
    # CSS 스타일 추가
    st.markdown("""
    <style>
/* 전체 페이지 스타일 */
.main-container {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 15px; /* 기존 20px에서 축소 */
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 15px; /* 기존 20px에서 축소 */
}

/* 섹션 스타일 */
.section-container {
    background-color: white;
    border-radius: 8px;
    padding: 10px; /* 기존 15px에서 축소 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    margin-bottom: 10px; /* 기존 15px에서 축소 */
}

/* 헤더 스타일 */
.section-header {
    color: #1f77b4;
    font-weight: 600;
    margin-bottom: 10px; /* 축소된 간격 */
    border-bottom: 2px solid #eaecef;
    padding-bottom: 6px; /* 축소된 패딩 */
}

/* 테이블 스타일 */
.process-table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin-bottom: 10px; /* 축소된 간격 */
}

.table-header {
    background-color: #f1f3f5;
    font-weight: 600;
    padding: 10px 12px; /* 축소된 패딩 */
    border-top: 1px solid #dee2e6;
    border-bottom: 2px solid #dee2e6;
    text-align: center;
}

.process-row {
    border-bottom: 1px solid #eaecef;
    transition: background-color 0.2s;
    padding: 5px 0; /* 축소된 패딩 */
    align-items: center;
}

.process-row:hover {
    background-color: #f8f9fa;
}

/* 버튼 스타일 개선 */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.3s ease;
    box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    padding: 0.4rem 0.8rem; /* 축소된 패딩 */
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.12);
}

/* 이동 버튼 스타일 */
.move-btn > button {
    padding: 0.2rem 0.4rem; /* 축소된 패딩 */
    min-height: 1.5rem; /* 축소된 높이 */
    line-height: 1;
    background-color: #f0f2f5;
    color: #444;
    border: 1px solid #ddd;
    width: 100%;
}

.move-btn > button:hover {
    background-color: #e0e4ea;
    color: #000;
}

/* 이동 버튼 컨테이너 */
.move-buttons-container {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin-top: 4px; /* 축소된 간격 */
}

/* 삭제 버튼 스타일 */
.delete-btn > button {
    background-color: #ff5a5a;
    color: white;
    border: none;
    width: 100%;
    padding: 0.4rem 0.8rem; /* 일관된 패딩 적용 */
}

.delete-btn > button:hover {
    background-color: #e03c3c;
}

/* 추가 버튼 스타일 */
.add-btn > button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 0.4rem 0.8rem; /* 축소된 패딩 */
    font-weight: 500;
}

.add-btn > button:hover {
    background-color: #3e8e41;
}

/* 저장 버튼 스타일 */
.save-btn > button {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 0.4rem 0.8rem; /* 축소된 패딩 */
    font-size: 0.95rem; /* 약간 축소된 글자 크기 */
    font-weight: 500;
    margin-top: 8px; /* 축소된 마진 */
}

.save-btn > button:hover {
    background-color: #0b7dda;
}

/* 공정 추가 영역 스타일 */
.add-process-area {
    display: flex;
    align-items: center;
    gap: 0.5rem; /* 축소된 간격 */
    margin-bottom: 0.5rem; /* 축소된 마진 */
    background-color: #f8f9fa;
    padding: 10px; /* 축소된 패딩 */
    border-radius: 8px;
    border: 1px dashed #ddd;
}

/* 셀렉트 박스 스타일 */
.select-container {
    min-width: 150px; /* 축소된 너비 */
}

/* 입력 필드 스타일 */
.stTextInput > div > div > input {
    border-radius: 6px;
    border: 1px solid #ddd;
    padding: 6px 10px; /* 축소된 패딩 */
}

.stNumberInput > div > div > input {
    border-radius: 6px;
    border: 1px solid #ddd;
    padding: 6px 10px; /* 축소된 패딩 */
}

/* 체크박스 스타일 */
.stCheckbox > label {
    font-weight: 500;
}

/* 순서 번호 스타일 */
.order-number {
    background-color: #f1f3f5;
    color: #495057;
    font-weight: 600;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    margin: 0 auto;
}

/* 공정 행 내 요소 정렬 */
.process-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 40px;
}

/* 공정 카드 스타일 - 행 단위 정렬 개선 */
.process-card {
    display: flex;
    align-items: center;
    padding: 5px; /* 축소된 패딩 */
    border-radius: 6px;
    border-bottom: 1px solid #eaecef;
    margin-bottom: 2px; /* 축소된 마진 */
}

/* 입력 컨테이너 */
.input-container {
    width: 100%;
    display: flex;
    align-items: center;
}
    </style>
    """, unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'processes' not in st.session_state:
        st.session_state.processes = []
        if selected_product in product_types:
            st.session_state.processes = copy_process_list(product_types[selected_product].processes)
    if 'current_product' not in st.session_state or st.session_state.current_product != selected_product:
        st.session_state.processes = []
        if selected_product in product_types:
            st.session_state.processes = copy_process_list(product_types[selected_product].processes)
        st.session_state.current_product = selected_product
    
    # 상태 변경 감지를 위한 세션 변수 초기화
    if 'need_update' not in st.session_state:
        st.session_state.need_update = False
    
    # 마지막 변경사항 추적을 위한 세션 변수
    if 'last_change_timestamp' not in st.session_state:
        st.session_state.last_change_timestamp = datetime.now()
    
    # 공정 이동 콜백 함수 - 위로 이동
    def move_up_callback(index):
        if index > 0:
            st.session_state.processes[index], st.session_state.processes[index-1] = st.session_state.processes[index-1], st.session_state.processes[index]
            st.session_state.last_change_timestamp = datetime.now()
            st.session_state.need_update = True
    
    # 공정 이동 콜백 함수 - 아래로 이동
    def move_down_callback(index):
        if index < len(st.session_state.processes) - 1:
            st.session_state.processes[index], st.session_state.processes[index+1] = st.session_state.processes[index+1], st.session_state.processes[index]
            st.session_state.last_change_timestamp = datetime.now()
            st.session_state.need_update = True
    
    # 공정 삭제 콜백 함수
    def delete_process_callback(index):
        if index < len(st.session_state.processes):
            st.session_state.processes.pop(index)
            st.session_state.last_change_timestamp = datetime.now()
            st.session_state.need_update = True
    
    # 공정 추가 위치 선택을 위한 세션 상태 초기화
    if 'add_position' not in st.session_state:
        st.session_state.add_position = "맨 아래"
    
    # 새 공정 이름 생성 함수 - 중복 방지
    def generate_new_process_name():
        base_name = "새 공정"
        existing_names = [p.name for p in st.session_state.processes]
        
        # 이미 '새 공정'이 있는 경우 번호를 붙임
        if base_name in existing_names:
            i = 1
            while f"{base_name} {i}" in existing_names:
                i += 1
            return f"{base_name} {i}"
        return base_name
    
    # 공정 추가 콜백 함수
    def add_process_callback():
        new_process_name = generate_new_process_name()
        new_process = Process(new_process_name, 5, 10, 1, False)
        
        # 선택한 위치에 공정 추가
        if st.session_state.add_position == "맨 위":
            st.session_state.processes.insert(0, new_process)
        elif st.session_state.add_position == "맨 아래":
            st.session_state.processes.append(new_process)
        else:
            # "공정 X 다음" 형식에서 인덱스 추출
            try:
                pos_str = st.session_state.add_position
                if "다음" in pos_str:
                    # "공정 X 다음" 형식에서 X 추출
                    idx_str = pos_str.split(" ")[1]
                    idx = int(idx_str) - 1  # 1부터 시작하는 인덱스를 0부터 시작하는 인덱스로 변환
                    
                    # 유효한 인덱스 범위 확인
                    if 0 <= idx < len(st.session_state.processes):
                        st.session_state.processes.insert(idx + 1, new_process)
                    else:
                        st.session_state.processes.append(new_process)
                else:
                    st.session_state.processes.append(new_process)
            except (ValueError, IndexError):
                # 파싱 오류 발생 시 기본값으로 맨 아래에 추가
                st.session_state.processes.append(new_process)
        
        st.session_state.last_change_timestamp = datetime.now()
        st.session_state.need_update = True
    
    # 변경사항 저장 함수
    def save_changes():
        # 현재 프로세스 순서 그대로 저장
        product_types[selected_product] = Product(selected_product, st.session_state.processes)
        save_product_types(product_types)
        st.success("변경사항이 저장되었습니다!")
        st.session_state.need_update = False
        st.rerun()
    
    # 메인 컨테이너 시작
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 공정 목록 섹션
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">공정 목록</h3>', unsafe_allow_html=True)
    
    # 테이블 헤더
    st.markdown('<div class="process-table">', unsafe_allow_html=True)
    col_header = st.columns([1, 2, 1, 1, 1, 1, 1])
    with col_header[0]:
        st.markdown('<div class="table-header">순서/이동</div>', unsafe_allow_html=True)
    with col_header[1]:
        st.markdown('<div class="table-header">공정명</div>', unsafe_allow_html=True)
    with col_header[2]:
        st.markdown('<div class="table-header">최소시간(분)</div>', unsafe_allow_html=True)
    with col_header[3]:
        st.markdown('<div class="table-header">최대시간(분)</div>', unsafe_allow_html=True)
    with col_header[4]:
        st.markdown('<div class="table-header">처리용량</div>', unsafe_allow_html=True)
    with col_header[5]:
        st.markdown('<div class="table-header">품질검사</div>', unsafe_allow_html=True)
    with col_header[6]:
        st.markdown('<div class="table-header">작업</div>', unsafe_allow_html=True)
    
    # 공정 목록 표시
    for i, process in enumerate(st.session_state.processes):
        st.markdown(f'<div class="process-row" id="process-{i}">', unsafe_allow_html=True)
        cols = st.columns([1, 2, 1, 1, 1, 1, 1])
        
        with cols[0]:
            # 순서 표시 및 이동 버튼
            st.markdown(f'<div class="order-number">{i+1}</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if i > 0:  # 첫 번째 항목이 아닌 경우에만 위로 버튼 표시
                    st.markdown('<div class="move-btn">', unsafe_allow_html=True)
                    st.button("↑", key=make_widget_key("up", i, st.session_state.last_change_timestamp), on_click=move_up_callback, args=(i,))
                    st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                if i < len(st.session_state.processes) - 1:  # 마지막 항목이 아닌 경우에만 아래로 버튼 표시
                    st.markdown('<div class="move-btn">', unsafe_allow_html=True)
                    st.button("↓", key=make_widget_key("down", i, st.session_state.last_change_timestamp), on_click=move_down_callback, args=(i,))
                    st.markdown('</div>', unsafe_allow_html=True)
            
        with cols[1]:
            name = st.text_input("공정명", value=process.name, key=make_widget_key("name", i, st.session_state.last_change_timestamp), label_visibility="collapsed")
        with cols[2]:
            min_time = st.number_input("최소시간", value=float(process.min_time), min_value=0.1, step=0.1, key=make_widget_key("min", i, st.session_state.last_change_timestamp), label_visibility="collapsed")
        with cols[3]:
            max_time = st.number_input("최대시간", value=float(process.max_time), min_value=float(min_time), step=0.1, key=make_widget_key("max", i, st.session_state.last_change_timestamp), label_visibility="collapsed")
        with cols[4]:
            capacity = st.number_input("처리용량", value=int(process.capacity), min_value=1, step=1, key=make_widget_key("cap", i, st.session_state.last_change_timestamp), label_visibility="collapsed")
        with cols[5]:
            is_quality_check = st.checkbox("품질검사", value=process.is_quality_check, key=make_widget_key("qc", i, st.session_state.last_change_timestamp), label_visibility="collapsed")
        with cols[6]:
            # 삭제 버튼
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            st.button("삭제", key=make_widget_key("del", i, st.session_state.last_change_timestamp), on_click=delete_process_callback, args=(i,))
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 입력값으로 프로세스 업데이트
        st.session_state.processes[i].name = name
        st.session_state.processes[i].min_time = min_time
        st.session_state.processes[i].max_time = max_time
        st.session_state.processes[i].capacity = capacity
        st.session_state.processes[i].is_quality_check = is_quality_check
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # 프로세스 테이블 종료
    st.markdown('</div>', unsafe_allow_html=True)  # 섹션 컨테이너 종료
    
    # 공정 추가 영역
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-header">공정 추가</h3>', unsafe_allow_html=True)
    
    # 공정 추가 위치 선택
    position_options = get_position_options(st.session_state.processes)
    
    # 공정 추가 영역 레이아웃 개선
    st.markdown('<div class="add-process-area">', unsafe_allow_html=True)
    
    # 추가 위치 선택 드롭다운
    st.markdown('<div class="select-container">', unsafe_allow_html=True)
    st.selectbox("추가 위치", position_options, key=make_widget_key("add_position", 0, st.session_state.last_change_timestamp), index=position_options.index(st.session_state.add_position) if st.session_state.add_position in position_options else 0, label_visibility="collapsed", on_change=lambda: setattr(st.session_state, 'add_position', st.session_state[make_widget_key("add_position", 0, st.session_state.last_change_timestamp)]))
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 공정 추가 버튼
    st.markdown('<div class="add-btn" style="flex-grow:1;">', unsafe_allow_html=True)
    st.button("공정 추가", key=make_widget_key("add_process_btn", 0, st.session_state.last_change_timestamp), on_click=add_process_callback)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # add-process-area 종료
    st.markdown('</div>', unsafe_allow_html=True)  # 섹션 컨테이너 종료
    
    # 저장 버튼
    st.markdown('<div class="save-btn">', unsafe_allow_html=True)
    if st.button("변경사항 저장", key=make_widget_key("save_btn", 0, st.session_state.last_change_timestamp), use_container_width=True):
        save_changes()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # 메인 컨테이너 종료

def run_simulation(product_type, num_products, simulation_time, progress_bar=None, random_seed=None):
    if random_seed:
        random.seed(random_seed)
    env = simpy.Environment()
    factory = FoodFactory(env, product_type)
    env.process(product_generator(env, factory, num_products))
    
    # 진행 상황 표시 기능 추가
    if progress_bar:
        start_time = time.time()
        while env.now < simulation_time:
            # 일정 시간 간격으로 시뮬레이션 실행
            env.run(until=min(env.now + 10, simulation_time))
            
            # 진행 상황 업데이트 (시간 기반 또는 제품 생성 기반 중 더 큰 값 사용)
            time_progress = min(env.now / simulation_time * 100, 100)
            product_progress = factory.progress
            overall_progress = max(time_progress, product_progress)
            
            # 진행 상황 표시 업데이트
            progress_bar.progress(overall_progress / 100, f"진행률: {overall_progress:.1f}% (시간: {env.now:.1f}/{simulation_time}분, 제품: {int(factory.progress * factory.total_products / 100)}/{factory.total_products}개)")
            
            # 실시간 업데이트를 위한 짧은 대기
            time.sleep(0.1)
    else:
        # 기존 방식으로 한 번에 실행
        env.run(until=simulation_time)
    
    return factory

def create_equipment_analysis(factory):
    analysis_data = []
    for name, monitor in factory.equipment_monitors.items():
        if monitor.request_count > 0:
            # 설비 가동률 = 총 처리 시간 / (시뮬레이션 시간 * 설비 용량)
            equipment_capacity = factory.equipment[name].capacity
            total_available_time = factory.env.now * equipment_capacity
            utilization = (monitor.total_process_time / total_available_time) * 100
            
            avg_wait_time = monitor.total_wait_time / monitor.request_count
            avg_process_time = monitor.total_process_time / monitor.completed_count if monitor.completed_count > 0 else 0
            
            throughput = monitor.completed_count / factory.env.now  # 단위 시간당 처리량
            wip = (monitor.request_count - monitor.completed_count)  # 현재 진행 중인 작업 수
            
            analysis_data.append({
                'process': name,
                'capacity': equipment_capacity,
                'utilization': utilization,
                'avg_wait_time': avg_wait_time,
                'avg_process_time': avg_process_time,
                'throughput': throughput,
                'wip': wip,
                'completed': monitor.completed_count,
                'failed': monitor.failed_count,
                'total_requests': monitor.request_count
            })
    
    # 분석 데이터가 없는 경우 빈 데이터프레임 반환
    if not analysis_data:
        return pd.DataFrame(columns=[
            'process', 'capacity', 'utilization', 'avg_wait_time', 'avg_process_time',
            'throughput', 'wip', 'completed', 'failed', 'total_requests'
        ])
    
    return pd.DataFrame(analysis_data)

def show_guide():
    st.markdown("""
    ## 👋 환영합니다!
    이 시뮬레이터는 식품 제조 공정을 모델링하고 분석하는 도구입니다.
    실제 공장의 생산 라인을 가상으로 구현하여 다양한 상황을 시뮬레이션하고, 
    결과를 분석할 수 있습니다.
    
    ### 🎯 주요 기능
    1. **생산 시뮬레이션**
       - 제품별 맞춤 공정 시뮬레이션
       - 실시간 생산 현황 모니터링
       - 불량률 및 품질 관리 분석
    
    2. **자원 분석**
       - 공정별 자원 활용률 분석
       - 대기 시간 및 처리 시간 분석
       - 병목 구간 식별
    
    3. **데이터 시각화**
       - 처리 시간 분포 분석
       - 실시간 성능 지표 대시보드
    
    ---
    
    ## 💻 사용 방법
    
    ### 1. 시뮬레이션 실행 탭
    
    #### 좌측 사이드바 설정
    - **제품 유형 선택**: 시뮬레이션할 제품 선택 (즉석식품, 음료 등)
    - **생산 제품 수**: 10-10000개 범위에서 설정
    - **시뮬레이션 시간**: 100-1000분 범위에서 설정
    - **시뮬레이션 시작** 버튼: 설정된 조건으로 시뮬레이션 실행
    
    #### 시뮬레이션 결과 화면
    1. **기본 통계**
       - 총 생산된 제품 수: 시뮬레이션 동안 완성된 제품의 총 개수
       - 평균 생산 시간: 전체 제품의 평균 생산 소요 시간
       - 최소/최대 생산 시간: 가장 빠른/느린 생산 시간
       - 불량률: 전체 생산 대비 불량 제품 비율
    
    2. **자원 활용률 분석**
       - 막대 그래프로 각 공정의 자원 활용률(%) 표시
       - 처리량(throughput): 단위 시간당 처리 제품 수
       - WIP(Work in Progress): 현재 진행 중인 작업 수
    
    3. **시간 분석 차트**
       - 대기 시간 vs 처리 시간 비교
       - 공정별 처리 시간 분포(박스플롯)
       - 공정별 대기 시간 분포(박스플롯)
    
    ### 2. 제품/공정 설정 탭
    
    #### 새 제품 추가
    1. 제품 이름 입력
    2. "새 제품 추가" 버튼 클릭
    
    #### 공정 설정
    1. 편집할 제품 선택
    2. 각 공정별 설정:
       - 공정명
       - 최소/최대 처리 시간(분)
       - 처리 용량(동시 처리 가능 수량)
    3. "공정 추가" 버튼: 새로운 공정 추가
    4. "삭제" 버튼: 해당 공정 삭제
    5. "변경사항 저장" 버튼: 수정된 내용 저장
    
    ---
    
    ## 📊 분석 지표 설명
    
    ### 1. 자원 활용률
    - 계산 방식: (총 처리 시간) / (시뮬레이션 시간 × 자원 용량) × 100
    - 의미: 각 공정의 설비가 얼마나 효율적으로 사용되는지 표시
    
    ### 2. 처리량(Throughput)
    - 계산 방식: 완료된 제품 수 / 시뮬레이션 시간
    - 의미: 단위 시간당 처리할 수 있는 제품의 수
    
    ### 3. WIP(Work in Progress)
    - 계산 방식: 요청된 작업 수 - 완료된 작업 수
    - 의미: 현재 공정에서 처리 중인 제품의 수
    
    ### 4. 대기 시간
    - 계산 방식: 자원 할당 시점 - 요청 시점
    - 의미: 각 공정에서 제품이 처리되기를 기다린 시간
    
    ---
    
    ## ⚠️ 주의사항
    1. 입력 데이터의 현실성
       - 처리 시간과 용량은 실제 공정을 반영하도록 설정
       - 비현실적인 값 입력 시 시뮬레이션 결과가 왜곡될 수 있음
    
    2. 시뮬레이션 한계
       - 실제 공정의 예상치 못한 변수는 반영되지 않음
       - 결과는 의사결정을 위한 참고 자료로 활용
    
    3. 데이터 저장
       - 공정 설정 변경 시 반드시 "변경사항 저장" 버튼 클릭
       - 저장하지 않은 변경사항은 유지되지 않음
    """)

def identify_bottlenecks(resource_analysis):
    """병목 구간을 식별하는 함수"""
    # 대기 시간이 가장 긴 공정을 병목 구간으로 식별
    if len(resource_analysis) == 0:
        # 빈 리스트 대신 빈 데이터프레임 반환
        return pd.DataFrame(columns=['process', 'avg_wait_time', 'utilization'])
    
    # 대기 시간 기준 정렬
    sorted_by_wait = resource_analysis.sort_values('avg_wait_time', ascending=False)
    
    # 상위 30% 이상의 대기 시간을 가진 공정을 병목 구간으로 식별
    threshold = sorted_by_wait['avg_wait_time'].max() * 0.7
    bottlenecks = sorted_by_wait[sorted_by_wait['avg_wait_time'] >= threshold]
    
    # 가동률이 높은 공정도 병목 구간으로 추가
    high_utilization = resource_analysis[resource_analysis['utilization'] >= 85]
    
    # 두 조건 중 하나라도 만족하는 공정을 병목 구간으로 식별
    bottlenecks = pd.concat([bottlenecks, high_utilization]).drop_duplicates()
    
    return bottlenecks

def suggest_optimal_capacity(resource_analysis, factory):
    """최적 설비 용량을 제안하는 함수"""
    # 분석 데이터가 비어있는 경우 빈 데이터프레임 반환
    if resource_analysis.empty:
        return pd.DataFrame(columns=[
            'process', 'current_capacity', 'suggested_capacity', 
            'utilization', 'avg_wait_time', 'reason'
        ])
        
    suggestions = []
    
    for _, row in resource_analysis.iterrows():
        process_name = row['process']
        current_capacity = row['capacity']
        utilization = row['utilization']
        avg_wait_time = row['avg_wait_time']
        
        # 가동률과 대기 시간을 기반으로 최적 용량 제안
        if utilization > 90 and avg_wait_time > 5:
            # 가동률이 매우 높고 대기 시간도 긴 경우 용량 증가 제안
            suggested_capacity = current_capacity + 2
            reason = "가동률이 매우 높고 대기 시간이 깁니다."
        elif utilization > 80 and avg_wait_time > 3:
            # 가동률이 높고 대기 시간이 있는 경우 용량 증가 제안
            suggested_capacity = current_capacity + 1
            reason = "가동률이 높고 대기 시간이 있습니다."
        elif utilization < 30 and current_capacity > 1:
            # 가동률이 낮고 현재 용량이 1보다 큰 경우 용량 감소 제안
            suggested_capacity = max(1, current_capacity - 1)
            reason = "가동률이 낮아 설비가 비효율적으로 사용되고 있습니다."
        else:
            # 그 외의 경우 현재 용량 유지
            suggested_capacity = current_capacity
            reason = "현재 설비 용량이 적절합니다."
        
        suggestions.append({
            'process': process_name,
            'current_capacity': current_capacity,
            'suggested_capacity': suggested_capacity,
            'utilization': utilization,
            'avg_wait_time': avg_wait_time,
            'reason': reason
        })
    
    return pd.DataFrame(suggestions)

def show_interpretation_guide():
    st.markdown("""
    # 📖 해석 방법 가이드
    
    이 시뮬레이션의 주요 지표와 데이터 해석 방법을 안내합니다.
    
    ## 주요 지표별 해석 및 계산식
    
    | 지표명 | 계산 로직/방법 | 의미 및 해석 |
    |-------|----------------|-------------|
    | **설비 가동률(%)** | 총처리시간 / (시뮬시간×용량) × 100 | 설비가 얼마나 효율적으로 사용되는지. 80~90% 이상이면 병목 가능성, 30% 이하면 과잉설비 가능성 |
    | **처리량(제품/분)** | 완료수 / 시뮬시간 | 단위 시간당 처리 제품 수. 높을수록 생산성 우수 |
    | **WIP** | 요청수 - 완료수 | 해당 공정에서 현재 진행 중(대기+처리)인 제품 수. 높으면 병목, 적정이면 흐름 원활 |
    | **평균 대기시간(분)** | 총대기시간 / 요청수 | 설비 부족/병목 지표. 5분 이상이면 설비 증설 고려 |
    | **평균 처리시간(분)** | 총처리시간 / 완료수 | 실제 처리 속도. 공정별 표준시간과 비교해 관리 |
    | **불량률/건수** | 불량수 / 전체수 | 품질 문제 지표. 불량률이 높으면 공정 개선 필요 |
    | **최적 용량 제안** | 가동률·대기시간 기반 | 설비 효율과 대기시간을 고려한 용량 조정 가이드 |
    | **상세 로그** | 각 이벤트별 기록 | 시뮬레이션의 모든 이벤트를 시간순으로 기록. 원인 분석, 추적에 활용 |
    
    ---
    
    ## 각 지표별 상세 설명
    
    ### 1. 설비 가동률(%)
    - **계산식**: 총 처리 시간 / (시뮬레이션 시간 × 설비 용량) × 100
    - **해석**: 100%에 가까울수록 설비가 항상 바쁘게 돌아감. 80~90% 이상이면 병목 가능성, 30% 이하면 과잉설비 가능성.
    
    ### 2. 처리량(제품/분)
    - **계산식**: 완료된 제품 수 / 시뮬레이션 시간
    - **해석**: 단위 시간당 처리 제품 수. 값이 높을수록 생산성이 높음.
    
    ### 3. WIP (Work In Progress)
    - **계산식**: 요청된 작업 수 - 완료된 작업 수
    - **해석**: 해당 공정에서 현재 처리 중이거나 대기 중인 제품 수. WIP가 높으면 병목 또는 설비 부족 가능성.
    
    ### 4. 평균 대기시간(분)
    - **계산식**: 총 대기 시간 / 요청된 작업 수
    - **해석**: 설비를 기다린 평균 시간. 5분 이상이면 설비 증설 또는 공정 개선 필요.
    
    ### 5. 평균 처리시간(분)
    - **계산식**: 총 처리 시간 / 완료된 작업 수
    - **해석**: 실제 처리 속도. 표준 처리시간과 비교해 관리.
    
    ### 6. 불량률/불량건수
    - **계산식**: 불량수 / 전체수 (품질검사 공정에서 passed=False)
    - **해석**: 품질 문제 지표. 불량률이 높으면 공정 개선 필요.
    
    ### 7. 최적 설비 용량 제안
    - **로직**: 가동률이 80~90% 이상이면서 평균 대기시간이 높으면 용량 증가 제안, 30% 이하이면서 용량이 1보다 크면 용량 감소 제안, 그 외는 현상 유지.
    - **해석**: 설비 효율과 대기시간을 고려한 용량 조정 가이드.
    
    ### 8. 상세 로그
    - **구성**: timestamp, product_id, process, wait_time, process_time, total_time, passed 등
    - **해석**: 시뮬레이션의 모든 이벤트를 시간순으로 기록. 병목, 불량, 대기시간 등 원인 분석에 활용.
    
    ---
    
    ## 실무 활용 팁
    - **가동률 80~90% 이상 + 대기시간↑**: 설비 증설/공정 개선 필요
    - **WIP↑**: 해당 공정이 병목, 설비 용량/공정 순서/작업자 배치 등 점검
    - **불량률↑**: 품질관리 강화, 원인 공정 추적
    - **상세 로그**: 특정 제품/공정/시간대별 문제 추적에 활용
    
    ## 참고
    - 각 지표는 실제 공장 운영 데이터와 비교해 해석하면 더욱 효과적입니다.
    - 시뮬레이션 결과는 의사결정 참고자료로 활용하세요.
    """)

def main():
    st.set_page_config(
        page_title="식품 공장 시뮬레이터",
        page_icon="🏭",
        layout="wide"
    )
    
    st.title('🏭 식품 공장 생산 라인 시뮬레이터')
    
    # 제품 타입 로드
    product_types = load_product_types()
    
    # 탭 생성 - 표준 Streamlit 탭 사용
    tab1, tab2, tab3, tab4 = st.tabs(["시뮬레이션 실행", "제품/공정 설정", "사용자 가이드", "해석 방법"])
    
    # 각 탭에 내용 추가
    with tab1:
        with st.sidebar:
            st.header('시뮬레이션 설정')
            selected_product = st.selectbox(
                '제품 유형',
                list(product_types.keys())
            )
            
            num_products = st.number_input(
                '생산 제품 수',
                min_value=10,
                max_value=10000,
                value=100,
                step=10
            )
            
            simulation_time = st.slider(
                '시뮬레이션 시간 (분)',
                min_value=100,
                max_value=1000,
                value=300
            )
            
            start_simulation = st.button('시뮬레이션 시작')
        
        if start_simulation:
            # 진행 상황 표시를 위한 프로그레스 바 추가
            progress_bar = st.progress(0, "시뮬레이션 준비 중...")
            
            with st.spinner('시뮬레이션 실행 중...'):
                factory = run_simulation(
                    product_types[selected_product],
                    num_products,
                    simulation_time,
                    progress_bar
                )
                
                # 기본 통계
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("총 생산된 제품 수", f"{len(factory.processing_times)}개")
                with col2:
                    st.metric("평균 생산 시간", f"{statistics.mean(factory.processing_times):.1f}분")
                with col3:
                    st.metric("최소 생산 시간", f"{min(factory.processing_times):.1f}분")
                with col4:
                    st.metric("최대 생산 시간", f"{max(factory.processing_times):.1f}분")
                with col5:
                    failure_rate = len(factory.failed_products) / num_products * 100
                    st.metric("불량률", f"{failure_rate:.1f}%")
                
                # 자원 활용률 분석
                st.subheader("공정별 설비 가동률 및 성능 분석")
                resource_analysis = create_equipment_analysis(factory)
                
                # resource_analysis가 비어있지 않은 경우에만 병목 구간 및 최적 용량 제안 분석 수행
                if not resource_analysis.empty:
                    # 병목 구간 식별
                    bottlenecks = identify_bottlenecks(resource_analysis)
                    if not bottlenecks.empty:
                        st.warning("⚠️ 병목 구간 감지")
                        st.write("다음 공정에서 병목 현상이 발생하고 있습니다:")
                        bottleneck_names = bottlenecks['process'].tolist()
                        for i, name in enumerate(bottleneck_names):
                            st.write(f"{i+1}. **{name}** - 평균 대기 시간: {bottlenecks[bottlenecks['process']==name]['avg_wait_time'].values[0]:.1f}분, 가동률: {bottlenecks[bottlenecks['process']==name]['utilization'].values[0]:.1f}%")
                    
                    # 최적 설비 용량 제안
                    st.subheader("최적 설비 용량 제안")
                    optimal_capacity = suggest_optimal_capacity(resource_analysis, factory)
                    
                    # 컬럼명 한글화
                    column_names = {
                        'process': '공정',
                        'current_capacity': '현재 용량',
                        'suggested_capacity': '제안 용량',
                        'utilization': '가동률(%)',
                        'avg_wait_time': '평균대기시간(분)',
                        'reason': '제안 이유'
                    }
                    optimal_capacity.columns = [column_names[col] for col in optimal_capacity.columns]
                    
                    # 현재 용량과 제안 용량이 다른 행만 강조 표시
                    def highlight_changes(row):
                        if row['현재 용량'] != row['제안 용량']:
                            return ['background-color: #FFFFCC' if col in ['제안 용량', '제안 이유'] else '' for col in row.index]
                        else:
                            return ['' for _ in row.index]
                    
                    # 데이터프레임 표시
                    st.dataframe(optimal_capacity.style.apply(highlight_changes, axis=1))
                else:
                    st.info("시뮬레이션 시간이 너무 짧거나 충분한 데이터가 수집되지 않았습니다. 시뮬레이션 시간을 늘리거나 제품 수를 늘려보세요.")
                
                # 설비 가동률 차트
                fig_utilization = px.bar(resource_analysis,
                                      x='process',
                                      y='utilization',
                                      title='공정별 설비 가동률 (%)',
                                      text='utilization')
                fig_utilization.update_traces(texttemplate='%{text:.1f}%')
                fig_utilization.update_layout(
                    xaxis_title="공정",
                    yaxis_title="설비 가동률 (%)",
                    yaxis_range=[0, 100]  # 0-100% 스케일 고정
                )
                st.plotly_chart(fig_utilization, use_container_width=True)
                
                # 처리량 및 WIP 분석
                col1, col2 = st.columns(2)
                with col1:
                    fig_throughput = px.bar(resource_analysis,
                                         x='process',
                                         y='throughput',
                                         title='공정별 처리량 (제품/분)')
                    fig_throughput.update_layout(
                        xaxis_title="공정",
                        yaxis_title="처리량 (제품/분)"
                    )
                    st.plotly_chart(fig_throughput, use_container_width=True)
                
                with col2:
                    fig_wip = px.bar(resource_analysis,
                                   x='process',
                                   y='wip',
                                   title='공정별 진행 중인 작업 수 (WIP)')
                    fig_wip.update_layout(
                        xaxis_title="공정",
                        yaxis_title="WIP"
                    )
                    st.plotly_chart(fig_wip, use_container_width=True)
                
                # 상세 분석 테이블 (개선된 버전)
                st.subheader("공정별 상세 성능 분석")
                display_cols = ['process', 'capacity', 'utilization', 'avg_wait_time', 
                              'avg_process_time', 'throughput', 'wip', 'completed', 
                              'failed', 'total_requests']
                formatted_analysis = resource_analysis[display_cols].copy()
                formatted_analysis['utilization'] = formatted_analysis['utilization'].round(1).astype(str) + '%'
                formatted_analysis['throughput'] = formatted_analysis['throughput'].round(3)
                formatted_analysis['avg_wait_time'] = formatted_analysis['avg_wait_time'].round(1)
                formatted_analysis['avg_process_time'] = formatted_analysis['avg_process_time'].round(1)
                
                # 컬럼명 한글화
                column_names = {
                    'process': '공정',
                    'capacity': '설비용량',
                    'utilization': '설비가동률',
                    'avg_wait_time': '평균대기시간',
                    'avg_process_time': '평균처리시간',
                    'throughput': '처리량(개/분)',
                    'wip': '진행중인작업',
                    'completed': '완료건수',
                    'failed': '불량건수',
                    'total_requests': '총요청건수'
                }
                formatted_analysis.columns = [column_names[col] for col in formatted_analysis.columns]
                formatted_analysis = rename_columns(formatted_analysis, column_names)
                st.dataframe(formatted_analysis, use_container_width=True)
                
                # 대기 시간 vs 처리 시간
                fig_times = go.Figure()
                fig_times.add_trace(go.Bar(name='평균 대기 시간',
                                         x=resource_analysis['process'],
                                         y=resource_analysis['avg_wait_time']))
                fig_times.add_trace(go.Bar(name='평균 처리 시간',
                                         x=resource_analysis['process'],
                                         y=resource_analysis['avg_process_time']))
                fig_times.update_layout(title='공정별 평균 대기 시간 vs 처리 시간',
                                      barmode='group')
                st.plotly_chart(fig_times, use_container_width=True)
                
                # 상세 분석 테이블
                st.subheader("공정별 상세 분석")
                st.dataframe(resource_analysis.round(2))
                
                # 공정별 처리 시간 분포
                st.subheader("공정별 처리 시간 분포")
                process_times_df = pd.DataFrame(factory.process_logs)
                fig = px.box(process_times_df, 
                            x='process', 
                            y='process_time',
                            title='공정별 처리 시간 분포')
                fig.update_layout(
                    xaxis_title="공정",
                    yaxis_title="처리 시간 (분)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 공정별 대기 시간 분포
                st.subheader("공정별 대기 시간 분포")
                fig_wait = px.box(process_times_df, 
                                x='process', 
                                y='wait_time',
                                title='공정별 대기 시간 분포')
                fig_wait.update_layout(
                    xaxis_title="공정",
                    yaxis_title="대기 시간 (분)"
                )
                st.plotly_chart(fig_wait, use_container_width=True)
                
                # 상세 로그 테이블
                st.subheader("상세 생산 로그")
                log_df = pd.DataFrame(factory.process_logs)
                log_df['timestamp'] = log_df['timestamp'].round(2)
                log_df['process_time'] = log_df['process_time'].round(2)
                log_df['wait_time'] = log_df['wait_time'].round(2)
                log_df['total_time'] = log_df['total_time'].round(2)
                st.dataframe(log_df)
    
    with tab2:
        st.header("제품 및 공정 설정")
        
        # 새 제품 추가
        new_product_name = st.text_input("새 제품 이름")
        
        # 입력값 검증
        is_valid_name = new_product_name.strip() != ""
        if new_product_name and not is_valid_name:
            st.error("제품 이름은 공백일 수 없습니다.")
        
        if st.button("새 제품 추가") and new_product_name:
            if not is_valid_name:
                st.error("유효한 제품 이름을 입력해주세요.")
            elif new_product_name in product_types:
                st.error("이미 존재하는 제품 이름입니다!")
            else:
                product_types[new_product_name] = Product(new_product_name, [])
                save_product_types(product_types)
                st.success(f"새 제품 '{new_product_name}'이(가) 추가되었습니다!")
                # 세션 상태 초기화
                if 'processes' in st.session_state:
                    del st.session_state.processes
                if 'current_product' in st.session_state:
                    del st.session_state.current_product
                st.rerun()
        
        # 제품 선택 및 편집
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_product_edit = st.selectbox(
                "편집할 제품 선택",
                list(product_types.keys()),
                key="edit_product"
            )
        
        with col2:
            if st.button("선택한 제품 삭제") and len(product_types) > 1:
                if st.session_state.get('confirm_delete', False):
                    # 제품 삭제 실행
                    del product_types[selected_product_edit]
                    save_product_types(product_types)
                    st.success(f"제품 '{selected_product_edit}'이(가) 삭제되었습니다!")
                    # 세션 상태 초기화
                    if 'processes' in st.session_state:
                        del st.session_state.processes
                    if 'current_product' in st.session_state:
                        del st.session_state.current_product
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning(f"정말 '{selected_product_edit}' 제품을 삭제하시겠습니까? 다시 한번 버튼을 클릭하면 삭제됩니다.")
            elif len(product_types) <= 1:
                st.warning("최소 1개 이상의 제품이 필요합니다.")
        
        # 삭제 확인 취소
        if st.session_state.get('confirm_delete', False):
            if st.button("삭제 취소"):
                st.session_state.confirm_delete = False
                st.rerun()
        
        edit_product_type(product_types, selected_product_edit)
    
    with tab3:
        show_guide()
    
    with tab4:
        show_interpretation_guide()

if __name__ == '__main__':
    main() 