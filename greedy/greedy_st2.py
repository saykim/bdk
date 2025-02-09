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
    max_profit = 0
    optimal_product = None
    optimal_production_amount = 0
    optimal_remaining_material_amounts = material_amounts
    for product in product_configurations:
        production_amount = min(material_amounts[i] / (product['configuration'][i] / 1000) for i in range(5))
        material_amounts_temp = [material_amounts[i] - production_amount * (product['configuration'][i] / 1000) for i in range(5)]
        profit, remaining_material_amounts = calculate_profit_and_loss(product, material_amounts_temp, material_prices)
        if profit * production_amount > max_profit:
            max_profit = profit * production_amount
            optimal_product = product
            optimal_production_amount = production_amount
            optimal_remaining_material_amounts = remaining_material_amounts

    return optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts

st.title("피자생산 계획 Copilot")

columns = st.columns(5)  # 5개의 열을 생성

material_amounts = [
    columns[0].text_input("도우 남은 재료량 (kg):", value="10"),
    columns[1].text_input("치즈1 남은 재료량 (kg):", value="10"),
    columns[2].text_input("치즈2 남은 재료량 (kg):", value="10"),
    columns[3].text_input("토핑1 남은 재료량 (kg):", value="10"),
    columns[4].text_input("토핑2 남은 재료량 (kg):", value="10")
]

material_prices = [700, 1000, 300, 500, 1200]  # kg 당 가격(원)

price_columns = st.columns(5)  # 5개의 열을 생성
for i, price_column in enumerate(price_columns):
    price_column.text(f"{material_prices[i]}원/kg")

product_configurations = [
    {'name': 'Product 327g', 'price': 3500, 'configuration': [100, 30, 20, 20, 40]},
    {'name': 'Product 347g', 'price': 4300, 'configuration': [110, 10, 30, 20, 50]},
    {'name': 'Product 407g', 'price': 4100, 'configuration': [150, 50, 40, 10, 30]}
]

st.markdown(
    """
    <style>
        .stButton>button {
            background-color: #FF5733;
            color: white;
            padding: 10px 100px;
            border-radius: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            text-align: left;
            padding: 8px;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.button('Calculate'):
    material_amounts = [float(amount) for amount in material_amounts]
    optimal_product, optimal_production_amount, max_profit, optimal_remaining_material_amounts = calculate_optimal_production(material_amounts, material_prices, product_configurations)
    
    st.markdown(
        f"* 최적의 제품: {optimal_product['name']} \n"
        f"* 생산 수량: {int(optimal_production_amount)} \n"
        f"* 이익금액: {int(max_profit):,}원 \n"
        f"* 남은 재료량: {sum(optimal_remaining_material_amounts):.2f}kg \n"
        f"* 남은 재료 금액: {int(sum(optimal_remaining_material_amounts[i] * material_prices[i] for i in range(5))):,}원"
    )

    data = {
        '제품': [product['name'] for product in product_configurations],
        '수량': [],
        '이익': [],
        '남은재료량': [],
        '남은 재료 금액': []
    }
    for product in product_configurations:
        production_amount = min(material_amounts[i] / (product['configuration'][i] / 1000) for i in range(5))
        profit, remaining_material_amounts = calculate_profit_and_loss(product, material_amounts, material_prices)
        data['수량'].append(f"{int(production_amount)}")
        data['이익'].append(f"{int(profit * production_amount):,}")
        data['남은재료량'].append(f"{sum(remaining_material_amounts):.2f}kg")
        data['남은 재료 금액'].append(f"{int(sum(remaining_material_amounts[i] * material_prices[i] for i in range(5))):,}원")

    df = pd.DataFrame(data)
    st.dataframe(df)
