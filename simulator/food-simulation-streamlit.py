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

class FoodFactory:
    def __init__(self, env, product_type):
        self.env = env
        self.product_type = product_type
        self.equipment = {}
        self.equipment_monitors = {}
        self.processing_times = []
        self.process_logs = []
        self.failed_products = []
        
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
    for i in range(num_products):
        yield env.timeout(random.uniform(2, 5))  # 이전 방식으로 복원
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
                    "capacity": p.capacity
                }
                for p in product.processes
            ]
        }
    
    # JSON 파일로 저장
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
                        p["capacity"]
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

def edit_product_type(product_types, selected_product):
    st.subheader(f"{selected_product} 공정 설정")
    
    processes = []
    if selected_product in product_types:
        processes = product_types[selected_product].processes
    
    process_data = []
    for i, process in enumerate(processes):
        st.write(f"공정 {i+1}")
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            name = st.text_input(f"공정명_{i}", value=process.name, key=f"name_{i}")
        with col2:
            min_time = st.number_input(f"최소시간(분)_{i}", value=process.min_time, key=f"min_{i}")
        with col3:
            max_time = st.number_input(f"최대시간(분)_{i}", value=process.max_time, key=f"max_{i}")
        with col4:
            capacity = st.number_input(f"처리용량_{i}", value=process.capacity, min_value=1, key=f"cap_{i}")
        with col5:
            if st.button("삭제", key=f"del_{i}"):
                continue
        
        process_data.append({
            "name": name,
            "min_time": min_time,
            "max_time": max_time,
            "capacity": capacity
        })
    
    if st.button("공정 추가"):
        process_data.append({
            "name": "새 공정",
            "min_time": 5,
            "max_time": 10,
            "capacity": 1
        })
    
    # 변경사항 저장
    if st.button("변경사항 저장"):
        processes = [Process(**p) for p in process_data]
        product_types[selected_product] = Product(selected_product, processes)
        save_product_types(product_types)
        st.success("변경사항이 저장되었습니다!")
        st.experimental_rerun()

def run_simulation(product_type, num_products, simulation_time):
    env = simpy.Environment()
    factory = FoodFactory(env, product_type)
    env.process(product_generator(env, factory, num_products))
    env.run(until=simulation_time)
    return factory

def create_gantt_chart(process_logs):
    df = pd.DataFrame(process_logs)
    df['end_time'] = df['timestamp'] + df['process_time']
    
    # 품질 검사 결과를 색상으로 표시
    df['상태'] = '정상'
    df.loc[df['passed'] == False, '상태'] = '불량'
    df.loc[df['passed'].isna(), '상태'] = '정상'
    
    fig = px.timeline(df, 
                     x_start='timestamp', 
                     x_end='end_time',
                     y='product_id',
                     color='process',
                     hover_data=['process_time', 'wait_time', '상태'],
                     title='생산 공정 간트 차트')
    
    fig.update_layout(
        height=600,
        xaxis_title="시간 (분)",
        yaxis_title="제품 번호",
        showlegend=True
    )
    return fig

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
       - 간트 차트로 생산 진행 현황 확인
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
    
    4. **간트 차트**
       - 가로축: 시간
       - 세로축: 제품 번호
       - 색상: 각 공정 구분
       - 호버 정보: 처리 시간, 대기 시간, 품질 검사 결과
    
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

def main():
    st.set_page_config(
        page_title="식품 공장 시뮬레이터",
        page_icon="🏭",
        layout="wide"
    )
    
    st.title('🏭 식품 공장 생산 라인 시뮬레이터')
    
    # 제품 타입 로드
    product_types = load_product_types()
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["시뮬레이션 실행", "제품/공정 설정", "사용자 가이드"])
    
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
            with st.spinner('시뮬레이션 실행 중...'):
                factory = run_simulation(
                    product_types[selected_product],
                    num_products,
                    simulation_time
                )
                
                # 기본 통계
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("평균 생산 시간", f"{statistics.mean(factory.processing_times):.1f}분")
                with col2:
                    st.metric("최소 생산 시간", f"{min(factory.processing_times):.1f}분")
                with col3:
                    st.metric("최대 생산 시간", f"{max(factory.processing_times):.1f}분")
                with col4:
                    failure_rate = len(factory.failed_products) / num_products * 100
                    st.metric("불량률", f"{failure_rate:.1f}%")
                
                # 자원 활용률 분석
                st.subheader("공정별 설비 가동률 및 성능 분석")
                resource_analysis = create_equipment_analysis(factory)
                
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
                
                # 간트 차트
                st.subheader("생산 공정 진행 현황")
                gantt_chart = create_gantt_chart(factory.process_logs)
                st.plotly_chart(gantt_chart, use_container_width=True)
                
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
        if st.button("새 제품 추가") and new_product_name:
            if new_product_name not in product_types:
                product_types[new_product_name] = Product(new_product_name, [])
                save_product_types(product_types)
                st.success(f"새 제품 '{new_product_name}'이(가) 추가되었습니다!")
                st.experimental_rerun()
            else:
                st.error("이미 존재하는 제품 이름입니다!")
        
        # 제품 선택 및 편집
        selected_product_edit = st.selectbox(
            "편집할 제품 선택",
            list(product_types.keys()),
            key="edit_product"
        )
        
        edit_product_type(product_types, selected_product_edit)
    
    with tab3:
        show_guide()

if __name__ == '__main__':
    main() 