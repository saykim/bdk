import streamlit as st
import pandas as pd
import altair as alt

# 유틸리티 함수
def validate_positive_float(value, field_name):
    try:
        float_value = float(value)
        if float_value <= 0:
            raise ValueError
        return float_value
    except ValueError:
        st.error(f"{field_name}은(는) 0보다 큰 숫자여야 합니다.")
        return None

# 손익 및 남은 재료량을 계산하는 함수
def calculate_profit_and_loss(product, material_amounts, material_prices):
    profit = product['price']
    remaining_material_amounts = material_amounts.copy()
    for i, usage in enumerate(product['configuration']):
        material_usage = usage / 1000  # g to kg 변환
        profit -= material_usage * material_prices[i]
        remaining_material_amounts[i] -= material_usage
    return profit, remaining_material_amounts

# 최적 생산 제품과 수량을 계산하는 함수
def calculate_optimal_production(material_amounts, material_prices, product_configurations):
    max_profit = float('-inf')
    optimal_product = None
    optimal_production_amount = 0
    optimal_remaining_material_amounts = material_amounts.copy()
    
    for product in product_configurations:
        production_amount = min(
            material_amounts[i] / (usage / 1000) if usage > 0 else float('inf')
            for i, usage in enumerate(product['configuration'])
        )
        if production_amount > 0 and production_amount != float('inf'):
            material_amounts_temp = [
                amount - production_amount * (usage / 1000)
                for amount, usage in zip(material_amounts, product['configuration'])
            ]
            profit, remaining_material_amounts = calculate_profit_and_loss(product, material_amounts_temp, material_prices)
            total_profit = profit * production_amount
            if total_profit > max_profit:
                max_profit = total_profit
                optimal_product = product
                optimal_production_amount = production_amount
                optimal_remaining_material_amounts = remaining_material_amounts.copy()

    return optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts

# Streamlit UI
st.title("피자 생산 계획 최적화")

# 사이드바에 입력 위젯 배치
with st.sidebar:
    st.header("재료 정보 입력")
    num_materials = st.number_input("재료의 종류 수:", min_value=1, value=5, step=1)
    
    material_amounts = []
    material_prices = []
    for i in range(num_materials):
        st.subheader(f"재료 {i+1}")
        amount = st.number_input(f"남은 재료량 (kg):", value=10.0, step=0.1, key=f"amount_{i}")
        price = st.number_input(f"가격 (원/kg):", value=1000, step=100, key=f"price_{i}")
        material_amounts.append(amount)
        material_prices.append(price)

    st.header("제품 정보 입력")
    num_products = st.number_input("제품의 종류 수:", min_value=1, value=3, step=1)

product_configurations = []
for i in range(num_products):
    st.subheader(f"제품 {i+1} 정보")
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input(f"제품 이름:", value=f"Product {i+1}", key=f"product_name_{i}")
    with col2:
        product_price = st.number_input(f"제품 가격 (원):", value=3500, step=100, key=f"product_price_{i}")
    
    st.write("재료 사용량 (g):")
    product_configuration = []
    cols = st.columns(num_materials)
    for j, col in enumerate(cols):
        with col:
            usage = st.number_input(f"재료 {j+1}", value=100, step=10, key=f"usage_{i}_{j}")
            product_configuration.append(usage)
    
    product_configurations.append({'name': product_name, 'price': product_price, 'configuration': product_configuration})

if st.button('최적화 계산'):
    if all(amount > 0 for amount in material_amounts) and all(price > 0 for price in material_prices):
        optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts = calculate_optimal_production(material_amounts, material_prices, product_configurations)
        
        if optimal_product:
            st.success("최적화 계산 완료!")
            st.write(f"최적의 제품: {optimal_product['name']}")
            st.write(f"최적 생산 수량: {int(optimal_production_amount)}개")
            st.write(f"예상 이익: {int(max_profit)}원")
            
            # 결과 시각화
            results_df = pd.DataFrame({
                '제품': [p['name'] for p in product_configurations],
                '생산량': [int(min(material_amounts[i] / (p['configuration'][i] / 1000) for i in range(num_materials))) for p in product_configurations],
                '예상 이익': [int(calculate_profit_and_loss(p, material_amounts, material_prices)[0] * min(material_amounts[i] / (p['configuration'][i] / 1000) for i in range(num_materials))) for p in product_configurations]
            })
            
            st.subheader("제품별 생산량 및 예상 이익")
            st.dataframe(results_df)
            
            # 막대 그래프로 시각화
            chart = alt.Chart(results_df).mark_bar().encode(
                x='제품',
                y='예상 이익',
                color='제품'
            ).properties(
                title='제품별 예상 이익'
            )
            st.altair_chart(chart, use_container_width=True)
            
            # 남은 재료량 표시
            st.subheader("최적 생산 후 남은 재료량")
            remaining_materials_df = pd.DataFrame({
                '재료': [f'재료 {i+1}' for i in range(num_materials)],
                '남은 양 (kg)': optimal_remaining_material_amounts,
                '남은 금액 (원)': [amount * price for amount, price in zip(optimal_remaining_material_amounts, material_prices)]
            })
            st.dataframe(remaining_materials_df)
        else:
            st.warning("최적의 생산 계획을 찾을 수 없습니다. 입력값을 확인해주세요.")
    else:
        st.error("모든 재료의 양과 가격은 0보다 커야 합니다. 입력값을 확인해주세요.")