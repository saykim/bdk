import streamlit as st
import pandas as pd
import numpy as np

def calculate_profit_and_loss(product, material_amounts, material_prices):
    profit = product['price']
    remaining_material_amounts = material_amounts.copy()
    for i in range(5):
        material_usage = product['configuration'][i] / 1000  # g to kg
        profit -= material_usage * material_prices[i]
        remaining_material_amounts[i] -= material_usage
    return profit, remaining_material_amounts

def calculate_optimal_production(material_amounts, material_prices, product_configurations):
    max_profit = float('-inf')
    optimal_product = None
    optimal_production_amount = 0
    optimal_remaining_material_amounts = material_amounts.copy()
    
    for product in product_configurations:
        production_amount = min(material_amounts[i] / (product['configuration'][i] / 1000) for i in range(5))
        if production_amount > 0:
            material_amounts_temp = [material_amounts[i] - production_amount * (product['configuration'][i] / 1000) for i in range(5)]
            profit, remaining_material_amounts = calculate_profit_and_loss(product, material_amounts_temp, material_prices)
            total_profit = profit * production_amount
            if total_profit > max_profit:
                max_profit = total_profit
                optimal_product = product
                optimal_production_amount = production_amount
                optimal_remaining_material_amounts = remaining_material_amounts.copy()

    return optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts

st.title("피자생산 계획")

st.markdown("재료의 남은 양(kg)을 입력하세요:")

columns = st.columns(5)
material_amounts = []
for i, label in enumerate(["도우", "치즈1", "치즈2", "토핑1", "토핑2"]):
    with columns[i]:
        amount = st.text_input(f"{label} 남은 재료량 (kg):", value="10")
        try:
            amount = float(amount)
            material_amounts.append(amount)
        except ValueError:
            st.error(f"{label}의 입력값이 유효하지 않습니다. 숫자를 입력해주세요.")

material_prices = [700, 1000, 300, 500, 1200]  # kg 당 가격(원)

st.markdown("재료의 가격 (원/kg):")
price_columns = st.columns(5)
for i, price in enumerate(material_prices):
    price_columns[i].text(f"{price}원/kg")

product_configurations = [
    {'name': 'Product 327g', 'price': 3500, 'configuration': [100, 30, 20, 20, 40]},
    {'name': 'Product 347g', 'price': 4300, 'configuration': [110, 10, 30, 20, 50]},
    {'name': 'Product 407g', 'price': 4100, 'configuration': [150, 50, 40, 10, 30]}
]

if st.button('계산'):
    if len(material_amounts) == 5:
        optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts = calculate_optimal_production(material_amounts, material_prices, product_configurations)
        if optimal_product:
            st.write(f"최적의 제품: {optimal_product['name']} | 생산 수량: {int(optimal_production_amount)} | 손익금액: {int(max_profit)}원 | 남은 재료량: {sum(optimal_remaining_material_amounts):.2f}kg | 남은 재료 금액: {int(sum(optimal_remaining_material_amounts[i] * material_prices[i] for i in range(5)))}원")

        data = {
            '제품': [product['name'] for product in product_configurations],
            '수량': [],
            '손익': [],
            '남은재료량': [],
            '남은 재료 금액': []
        }
        for product in product_configurations:
            production_amount = min(material_amounts[i] / (product['configuration'][i] / 1000) for i in range(5))
            if production_amount > 0:
                profit, remaining_material_amounts = calculate_profit_and_loss(product, material_amounts, material_prices)
                data['수량'].append(f"{int(production_amount)}")
                data['손익'].append(f"{int(profit * production_amount)}")
                data['남은재료량'].append(f"{sum(remaining_material_amounts):.2f}kg")
                data['남은 재료 금액'].append(f"{int(sum(remaining_material_amounts[i] * material_prices[i] for i in range(5)))}원")
            else:
                data['수량'].append("0")
                data['손익'].append("0")
                data['남은재료량'].append(f"{sum(material_amounts):.2f}kg")
                data['남은 재료 금액'].append(f"{int(sum(material_amounts[i] * material_prices[i] for i in range(5)))}원")
        
        df = pd.DataFrame(data)
        st.table(df)
    else:
        st.error("모든 재료량을 입력해주세요.")
