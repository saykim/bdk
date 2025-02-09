import streamlit as st
import pandas as pd
import altair as alt
from typing import List, Dict, Tuple, Union, Optional
import plotly.graph_objects as go

# 스타일 및 레이아웃 설정
st.set_page_config(layout="wide", page_title="피자 생산 최적화")

# CSS를 사용한 스타일 개선
st.markdown("""
<style>
    .reportview-container .main .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1E3A8A;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
    }
    .stTextInput>div>div>input {
        border-color: #1E3A8A;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 타입 정의
Material = Tuple[float, float]  # (amount, price)
Product = Dict[str, Union[str, float, List[float]]]

def validate_positive_float(value: float, field_name: str) -> Optional[float]:
    """입력값이 양수인지 검증"""
    try:
        float_value = float(value)
        if float_value <= 0:
            raise ValueError
        return float_value
    except ValueError:
        st.error(f"{field_name}은(는) 0보다 큰 숫자여야 합니다.")
        return None

def calculate_profit_and_loss(product: Product, material_amounts: List[float], material_prices: List[float]) -> Tuple[float, List[float]]:
    """손익 및 남은 재료량 계산"""
    profit = product['price']
    remaining_material_amounts = material_amounts.copy()
    for i, usage in enumerate(product['configuration']):
        material_usage = usage / 1000  # g to kg 변환
        profit -= material_usage * material_prices[i]
        remaining_material_amounts[i] -= material_usage
    return profit, remaining_material_amounts

def calculate_optimal_production(materials: List[Material], products: List[Product]) -> Tuple[Optional[Product], float, float, List[float]]:
    """최적 생산 계획 계산"""
    material_amounts, material_prices = zip(*materials)
    max_profit = float('-inf')
    optimal_product = None
    optimal_production_amount = 0
    optimal_remaining_material_amounts = list(material_amounts)
    
    for product in products:
        production_amount = min(
            amount / (usage / 1000) if usage > 0 else float('inf')
            for amount, usage in zip(material_amounts, product['configuration'])
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

def create_input_widgets() -> Tuple[List[Material], List[Product]]:
    """입력 위젯 생성"""
    with st.sidebar:
        st.sidebar.header("📊 재료 및 제품 정보 입력")
        num_materials = st.number_input("재료의 종류 수:", min_value=1, value=5, step=1)
        
        materials = []
        for i in range(num_materials):
            st.sidebar.subheader(f"🥫 재료 {i+1}")
            amount = st.number_input(f"남은 재료량 (kg):", value=10.0, step=0.1, key=f"amount_{i}", format="%.1f")
            price = st.number_input(f"가격 (원/kg):", value=1000, step=100, key=f"price_{i}")
            materials.append((amount, price))

        st.sidebar.header("🍕 제품 정보 입력")
        num_products = st.number_input("제품의 종류 수:", min_value=1, value=3, step=1)

    products = []
    for i in range(num_products):
        st.subheader(f"제품 {i+1} 정보")
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input(f"제품 이름:", value=f"피자 {i+1}", key=f"product_name_{i}")
        with col2:
            product_price = st.number_input(f"제품 가격 (원):", value=15000, step=500, key=f"product_price_{i}")
        
        st.write("재료 사용량 (g):")
        product_configuration = []
        cols = st.columns(num_materials)
        for j, col in enumerate(cols):
            with col:
                usage = st.number_input(f"재료 {j+1}", value=100, step=10, key=f"usage_{i}_{j}")
                product_configuration.append(usage)
        
        products.append({'name': product_name, 'price': product_price, 'configuration': product_configuration})

    return materials, products

def visualize_results(products: List[Product], materials: List[Material], optimal_product: Product, optimal_production_amount: float, max_profit: float, optimal_remaining_material_amounts: List[float]):
    """결과 시각화"""
    st.success("✅ 최적화 계산 완료!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("최적의 제품", optimal_product['name'])
    col2.metric("최적 생산 수량", f"{int(optimal_production_amount)}개")
    col3.metric("예상 이익", f"{int(max_profit):,}원")
    
    results_df = pd.DataFrame({
        '제품': [p['name'] for p in products],
        '생산량': [int(min(materials[i][0] / (p['configuration'][i] / 1000) for i in range(len(materials)))) for p in products],
        '예상 이익': [int(calculate_profit_and_loss(p, [m[0] for m in materials], [m[1] for m in materials])[0] * 
                     min(materials[i][0] / (p['configuration'][i] / 1000) for i in range(len(materials)))) for p in products]
    })
    
    st.subheader("📊 제품별 생산량 및 예상 이익")
    
    # Plotly를 사용한 인터랙티브 차트
    fig = go.Figure(data=[
        go.Bar(name='생산량', x=results_df['제품'], y=results_df['생산량']),
        go.Bar(name='예상 이익', x=results_df['제품'], y=results_df['예상 이익'])
    ])
    fig.update_layout(barmode='group', title='제품별 생산량 및 예상 이익')
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(results_df.style.highlight_max(axis=0), use_container_width=True)
    
    st.subheader("🧮 최적 생산 후 남은 재료량")
    remaining_materials_df = pd.DataFrame({
        '재료': [f'재료 {i+1}' for i in range(len(materials))],
        '남은 양 (kg)': [f"{amount:.2f}" for amount in optimal_remaining_material_amounts],
        '남은 금액 (원)': [f"{int(amount * price):,}" for amount, (_, price) in zip(optimal_remaining_material_amounts, materials)]
    })
    st.dataframe(remaining_materials_df.style.highlight_min(axis=0), use_container_width=True)

def main():
    st.title("🍕 피자 생산 계획 최적화")
    st.markdown("---")

    materials, products = create_input_widgets()

    if st.button('🚀 최적화 계산', key='optimize'):
        with st.spinner('계산 중...'):
            if all(amount > 0 and price > 0 for amount, price in materials):
                optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts = calculate_optimal_production(materials, products)
                
                if optimal_product:
                    visualize_results(products, materials, optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts)
                else:
                    st.warning("⚠️ 최적의 생산 계획을 찾을 수 없습니다. 입력값을 확인해주세요.")
            else:
                st.error("❌ 모든 재료의 양과 가격은 0보다 커야 합니다. 입력값을 확인해주세요.")

if __name__ == "__main__":
    main()