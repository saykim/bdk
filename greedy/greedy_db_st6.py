import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import json
from typing import List, Dict, Tuple, Union, Optional

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
Product = Dict[str, Union[int, str, float, List[float]]]

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
    profit = float(product['price'])
    remaining_material_amounts = material_amounts.copy()
    for i, usage in enumerate(product['configuration']):
        material_usage = usage / 1000  # g to kg 변환
        profit -= material_usage * material_prices[i]
        remaining_material_amounts[i] = max(0, remaining_material_amounts[i] - material_usage)
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
            (amount / (usage / 1000) if usage > 0 else float('inf'))
            for amount, usage in zip(material_amounts, product['configuration'])
        )
        if production_amount > 0 and production_amount != float('inf'):
            material_amounts_temp = [
                max(0, amount - production_amount * (usage / 1000))
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

def visualize_results(products: List[Product], materials: List[Material], optimal_product: Product, optimal_production_amount: float, max_profit: float, optimal_remaining_material_amounts: List[float]):
    """결과 시각화"""
    st.success("✅ 최적화 계산 완료!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("최적의 제품", optimal_product['name'])
    col2.metric("최적 생산 수량", f"{int(optimal_production_amount)}개")
    col3.metric("예상 이익", f"{int(max_profit):,}원")
    
    def safe_production_amount(product, materials):
        try:
            return int(min(
                materials[i][0] / (product['configuration'][i] / 1000)
                for i in range(min(len(materials), len(product['configuration'])))
                if product['configuration'][i] > 0
            ))
        except ValueError:
            return 0  # 생산 불가능한 경우

    def safe_profit_calculation(product, materials):
        try:
            profit, _ = calculate_profit_and_loss(
                product, 
                [m[0] for m in materials[:len(product['configuration'])]], 
                [m[1] for m in materials[:len(product['configuration'])]]
            )
            production_amount = safe_production_amount(product, materials)
            return int(profit * production_amount)
        except:
            return 0  # 계산 불가능한 경우

    results_df = pd.DataFrame({
        '제품': [p['name'] for p in products],
        '생산량': [safe_production_amount(p, materials) for p in products],
        '예상 이익': [safe_profit_calculation(p, materials) for p in products]
    })
    
    st.subheader("📊 제품별 생산량 및 예상 이익")
    
    fig = go.Figure(data=[
        go.Bar(name='생산량', x=results_df['제품'], y=results_df['생산량']),
        go.Bar(name='예상 이익', x=results_df['제품'], y=results_df['예상 이익'])
    ])
    fig.update_layout(barmode='group', title='제품별 생산량 및 예상 이익')
    st.plotly_chart(fig, use_container_width=True)
    
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: yellow' if v else '' for v in is_max]
    
    st.dataframe(results_df.style.apply(highlight_max, subset=['예상 이익']), use_container_width=True)
    
    st.subheader("🧮 최적 생산 후 남은 재료량")
    remaining_materials_df = pd.DataFrame({
        '재료': [f'재료 {i+1}' for i in range(len(materials))],
        '남은 양 (kg)': [f"{max(0, amount):.2f}" for amount in optimal_remaining_material_amounts],
        '남은 금액 (원)': [f"{int(max(0, amount) * price):,}" for amount, (_, price) in zip(optimal_remaining_material_amounts, materials)]
    })
    st.dataframe(remaining_materials_df, use_container_width=True)

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    try:
        conn = sqlite3.connect('pizza_products.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY, name TEXT, price REAL, configuration TEXT)''')
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"데이터베이스 초기화 오류: {e}")
    finally:
        conn.close()

def save_product(product: Product):
    """제품 정보를 데이터베이스에 저장"""
    try:
        conn = sqlite3.connect('pizza_products.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name, price, configuration) VALUES (?, ?, ?)",
                  (product['name'], product['price'], json.dumps(product['configuration'])))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"제품 저장 오류: {e}")
    finally:
        conn.close()

def load_products() -> List[Product]:
    """데이터베이스에서 모든 제품 정보 로드"""
    try:
        conn = sqlite3.connect('pizza_products.db')
        c = conn.cursor()
        c.execute("SELECT id, name, price, configuration FROM products")
        rows = c.fetchall()
        return [{'id': row[0], 'name': row[1], 'price': row[2], 'configuration': json.loads(row[3])} for row in rows]
    except sqlite3.Error as e:
        st.error(f"제품 로드 오류: {e}")
        return []
    finally:
        conn.close()

def update_product(product_id: int, product: Product):
    """제품 정보 업데이트"""
    try:
        conn = sqlite3.connect('pizza_products.db')
        c = conn.cursor()
        c.execute("UPDATE products SET name=?, price=?, configuration=? WHERE id=?",
                  (product['name'], product['price'], json.dumps(product['configuration']), product_id))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"제품 업데이트 오류: {e}")
    finally:
        conn.close()

def delete_product(product_id: int):
    """제품 삭제"""
    try:
        conn = sqlite3.connect('pizza_products.db')
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"제품 삭제 오류: {e}")
    finally:
        conn.close()

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

    st.header("🍕 제품 정보 관리")
    products = load_products()
    
    # 새 제품 추가
    with st.expander("새 제품 추가"):
        new_product = {}
        new_product['name'] = st.text_input("제품 이름:")
        new_product['price'] = st.number_input("제품 가격 (원):", value=0.0, min_value=0.0, step=500.0, format="%.1f")
        new_product['configuration'] = [st.number_input(f"재료 {i+1} 사용량 (g):", value=0.0, min_value=0.0, step=10.0, format="%.1f") for i in range(num_materials)]
        if st.button("제품 추가"):
            save_product(new_product)
            st.success("제품이 추가되었습니다.")
            st.experimental_rerun()

    # 기존 제품 관리
    for product in products:
        with st.expander(f"제품: {product['name']}"):
            updated_product = product.copy()
            updated_product['name'] = st.text_input(f"제품 이름:", value=product['name'], key=f"update_name_{product['id']}")
            updated_product['price'] = st.number_input(f"제품 가격 (원):", value=float(product['price']), min_value=0.0, step=500.0, format="%.1f", key=f"update_price_{product['id']}")
            # 현재 재료 수에 맞게 configuration 조정
            while len(updated_product['configuration']) < num_materials:
                updated_product['configuration'].append(0.0)
            updated_product['configuration'] = updated_product['configuration'][:num_materials]
            updated_product['configuration'] = [
                st.number_input(f"재료 {j+1} 사용량 (g):", value=float(usage), min_value=0.0, step=10.0, format="%.1f", key=f"update_usage_{product['id']}_{j}")
                for j, usage in enumerate(updated_product['configuration'])
            ]
            col1, col2 = st.columns(2)
            with col1:
                if st.button("업데이트", key=f"update_{product['id']}"):
                    update_product(product['id'], updated_product)
                    st.success("제품 정보가 업데이트되었습니다.")
                    st.experimental_rerun()
            with col2:
                if st.button("삭제", key=f"delete_{product['id']}"):
                    delete_product(product['id'])
                    st.success("제품이 삭제되었습니다.")
                    st.experimental_rerun()

    return materials, products

def main():
    st.title("🍕 피자 생산 계획 최적화")
    st.markdown("---")

    init_db()  # 데이터베이스 초기화
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