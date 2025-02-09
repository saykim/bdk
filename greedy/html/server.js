const express = require('express');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

app.post('/calculate', (req, res) => {
    const { materialAmounts, materialPrices, productConfigurations } = req.body;

    // 각 제품별 이익과 재료 손실을 계산
    const calculateProfitAndLoss = (product) => {
        let profit = product.price;
        let loss = 0;
        for (let i = 0; i < 5; i++) {
            const materialUsage = product.configuration[i] / 1000;  // g to kg
            profit -= materialUsage * materialPrices[i];
            loss += (materialAmounts[i] - materialUsage) * materialPrices[i];
        }
        return { profit, loss };
    };

    // 각 제품에 대해 이익과 재료 손실을 계산하고 최적의 제품을 찾음
    let optimalProduct = null;
    let maxProfit = 0;
    for (const product of productConfigurations) {
        const { profit, loss } = calculateProfitAndLoss(product);
        if (profit > maxProfit) {
            maxProfit = profit;
            optimalProduct = product;
        }
    }

    res.json({ optimalProduct, maxProfit });
});

app.listen(3000, () => {
    console.log('Server is running on port 3000');
});
