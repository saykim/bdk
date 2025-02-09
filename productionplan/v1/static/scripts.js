// 전역 변수 선언
let plans = [];
let products = [];
let productMap = {};
let currentStartDate = new Date();
const tooltip = document.getElementById('tooltip');
let colorMap = {};
const colors = [
    '#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b',
    '#27ae60', '#2980b9', '#8e44ad', '#f39c12', '#d35400'
];

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    currentStartDate = getWeekStart(new Date());
    getProductsList().then(() => {
        loadData();
    });

    // 제품 선택 시 BOM 자동 업데이트
    const productSelect = document.getElementById('productSelect');
    const bomSelect = document.getElementById('bom');
    
    productSelect.addEventListener('change', function() {
        const selectedProductName = this.value;
        bomSelect.innerHTML = '<option value="">BOM 선택</option>';
        
        if (selectedProductName && productMap[selectedProductName]) {
            const products = productMap[selectedProductName];
            console.log('선택된 제품의 BOM 목록:', products); // 디버깅용
            
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;  // BOM 선택 시 제품 ID 저장
                option.textContent = product.bom;
                bomSelect.appendChild(option);
            });
        }
    });
});

// 유틸리티 함수
function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setDate(diff);
    d.setHours(0,0,0,0);
    return d;
}

// 네비게이션 함수들
function prevWeek() {
    currentStartDate.setDate(currentStartDate.getDate() - 7);
    renderGantt();
}

function nextWeek() {
    currentStartDate.setDate(currentStartDate.getDate() + 7);
    renderGantt();
}

function currentWeek() {
    currentStartDate = getWeekStart(new Date());
    renderGantt();
}

// 데이터 관련 함수들
function getProductsList() {
    return fetch('/get_products')
        .then(res => res.json())
        .then(data => {
            console.log('서버 응답:', data); // 디버깅용
            products = data.products;
            productMap = {};  // productMap 초기화
            
            const productSelect = document.getElementById('productSelect');
            productSelect.innerHTML = '<option value="">제품 선택</option>';
            
            // 제품명으로 그룹화
            const uniqueProductNames = new Set();
            products.forEach(product => {
                uniqueProductNames.add(product.product_name);
                productMap[product.product_name] = products.filter(p => 
                    p.product_name === product.product_name
                );
            });
            
            // 고유한 제품명만 추가
            uniqueProductNames.forEach(productName => {
                const option = document.createElement('option');
                option.value = productName;
                option.textContent = productName;
                productSelect.appendChild(option);
            });
        });
}

function addPlan() {
    const productName = document.getElementById('productSelect').value;
    const selectedProductId = document.getElementById('bom').value;
    
    if (!productName || !selectedProductId) {
        alert('제품과 BOM을 선택해주세요.');
        return;
    }

    // 선택된 제품 정보 찾기
    const selectedProduct = products.find(p => p.id.toString() === selectedProductId);
    if (!selectedProduct) {
        alert('선택된 제품 정보를 찾을 수 없습니다.');
        return;
    }

    // 필수 입력값 검증
    const date = document.getElementById('date').value;
    const startTime = document.getElementById('startTime').value;
    const duration = document.getElementById('duration').value;
    const line = document.getElementById('line').value;
    const quantity = document.getElementById('quantity').value;

    if (!date || !startTime || !duration || !line || !quantity) {
        alert('모든 필수 항목을 입력해주세요.');
        return;
    }
    
    const data = {
        date: date,
        start_time: startTime,
        duration: parseFloat(duration),
        line: parseInt(line),
        product_id: parseInt(selectedProductId),
        product_name: selectedProduct.product_name,
        bom: selectedProduct.bom,
        quantity: parseInt(quantity),
        notes: document.getElementById('notes').value || ''
    };

    console.log('서버로 보내는 데이터:', data); // 디버깅용

    fetch('/add_plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => {
                throw new Error(err.message || '계획 추가 실패');
            });
        }
        return res.json();
    })
    .then(result => {
        if (result.success) {
            loadData();
            // 입력 필드 초기화
            document.getElementById('date').value = '';
            document.getElementById('startTime').value = '';
            document.getElementById('duration').value = '';
            document.getElementById('line').value = '';
            document.getElementById('productSelect').value = '';
            document.getElementById('bom').value = '';
            document.getElementById('quantity').value = '';
            document.getElementById('notes').value = '';
        } else {
            alert('계획 추가 실패: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
}

// 렌더링 함수들
function renderYAxis() {
    const ganttLines = document.querySelector('.gantt-lines');
    ganttLines.innerHTML = '';

    const lineLabelsContainer = document.createElement('div');
    lineLabelsContainer.className = 'line-labels-container';

    // 위치 기준 설정 - 높이 증가
    lineLabelsContainer.style.position = 'relative';
    lineLabelsContainer.style.height = (15 * 45) + 'px'; // 30px에서 45px로 증가
    lineLabelsContainer.style.width = '50px';

    for (let i = 1; i <= 15; i++) {
        const lineLabel = document.createElement('div');
        lineLabel.className = 'line-label';
        lineLabel.textContent = i + '호기';

        lineLabel.style.position = 'absolute';
        lineLabel.style.top = ((i - 1) * 45) + 'px'; // 30px에서 45px로 증가
        lineLabel.style.height = '45px'; // 30px에서 45px로 증가
        lineLabel.style.lineHeight = '45px'; // 30px에서 45px로 증가
        lineLabel.style.whiteSpace = 'nowrap';

        lineLabelsContainer.appendChild(lineLabel);
    }

    ganttLines.appendChild(lineLabelsContainer);
}

function renderGantt() {
    renderYAxis();
    
    const ganttGrid = document.querySelector('.gantt-grid');
    const dateScale = document.querySelector('.date-scale');
    const timeScale = document.querySelector('.time-scale');

    // 데이터가 없을 경우 처리
    if (plans.length === 0) {
        timeScale.innerHTML = '';
        dateScale.innerHTML = '';
        ganttGrid.innerHTML = '';
        return;
    }

    // 주간 날짜 범위 설정
    let weekEnd = new Date(currentStartDate);
    weekEnd.setDate(weekEnd.getDate() + 7);

    // 날짜 스케일 렌더링
    dateScale.innerHTML = '';
    for (let d = new Date(currentStartDate); d < weekEnd; d.setDate(d.getDate() + 1)) {
        const marker = document.createElement('div');
        marker.className = 'date-marker';
        const leftPercent = ((d - currentStartDate) / (weekEnd - currentStartDate)) * 100;
        marker.style.left = leftPercent + '%';
        marker.textContent = `${d.getMonth()+1}/${d.getDate()}`;
        dateScale.appendChild(marker);
    }

    // 시간 스케일 렌더링
    timeScale.innerHTML = '';
    for (let h = 0; h < 24; h += 2) {
        const marker = document.createElement('div');
        marker.className = 'time-marker';
        marker.style.left = (h / 24 * 100) + '%';
        marker.textContent = `${String(h).padStart(2,'0')}:00`;
        timeScale.appendChild(marker);
    }

    // 격자 생성
    ganttGrid.innerHTML = '';
    for (let i = 0; i < 15; i++) {
        const row = document.createElement('div');
        row.className = 'gantt-row';
        row.style.top = (i * 45) + 'px';  // 30px에서 45px로 증가
        ganttGrid.appendChild(row);
    }

    // 간트 바 렌더링
    plans.forEach(plan => {
        const startDate = new Date(plan.date + 'T' + plan.start_time);
        const endDate = new Date(plan.end_time.replace(' ', 'T'));
        
        // 현재 표시 범위를 벗어나면 건너뛰기
        if (startDate >= weekEnd || endDate <= currentStartDate) return;
        
        const totalMs = weekEnd - currentStartDate;
        const leftPercent = Math.max(0, (startDate - currentStartDate) / totalMs * 100);
        const widthPercent = Math.min(100 - leftPercent, (endDate - startDate) / totalMs * 100);

        const bar = document.createElement('div');
        bar.className = 'gantt-bar' + (plan.done ? ' done' : '');
        
        // 위치와 크기 설정
        bar.style.left = leftPercent + '%';
        bar.style.width = widthPercent + '%';
        bar.style.top = ((plan.line - 1) * 45) + 'px';  // 30px에서 45px로 증가
        bar.style.height = '39px';  // 24px에서 39px로 증가
        
        // 제품명과 BOM에 따른 색상 설정
        if (!plan.done) {
            bar.style.background = getColorForProduct(plan.product_name, plan.bom);
        }
        
        // 제품명과 BOM 함께 표시
        bar.textContent = `${plan.product_name} (${plan.bom})`;
        
        // 툴팁 이벤트
        bar.addEventListener('mouseover', (e) => {
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = `
                <div>제품: ${plan.product_name}</div>
                <div>BOM: ${plan.bom}</div>
                <div>수량: ${plan.quantity}</div>
                <div>시작: ${plan.start_time}</div>
                <div>종료: ${plan.end_time}</div>
                ${plan.notes ? `<div>비고: ${plan.notes}</div>` : ''}
            `;
            tooltip.style.display = 'block';
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY + 10 + 'px';
        });
        
        bar.addEventListener('mousemove', (e) => {
            const tooltip = document.getElementById('tooltip');
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY + 10 + 'px';
        });

        bar.addEventListener('mouseout', () => {
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'none';
        });

        ganttGrid.appendChild(bar);
    });
}

function renderTable() {
    const tbody = document.querySelector('#planTable tbody');
    tbody.innerHTML = '';
    plans.forEach(plan => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${plan.id}</td>
            <td>${plan.date}</td>
            <td>${plan.start_time}</td>
            <td>${plan.duration}</td>
            <td>${plan.end_time}</td>
            <td>${plan.line}</td>
            <td>${plan.product_name}</td>
            <td>${plan.bom}</td>
            <td>${plan.quantity}</td>
            <td>${plan.notes}</td>
            <td>
                <button onclick="editPlan(${plan.id})">수정</button>
                <button onclick="deletePlan(${plan.id})">삭제</button>
                ${plan.done == 1 ? 
                    `<button onclick="undonePlan(${plan.id})">완료취소</button>` :
                    `<button onclick="donePlan(${plan.id})">완료</button>`}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderSummary() {
    fetch('/summary')
        .then(res => res.json())
        .then(data => {
            const tbody = document.querySelector('#summaryTable tbody');
            tbody.innerHTML = '';
            data.summary.forEach(s => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${s.date}</td>
                    <td>${s.product_name}</td>
                    <td>${s.bom}</td>
                    <td>${s.total_qty}</td>
                `;
                tbody.appendChild(tr);
            });
        });
}

// CRUD 작업 함수들
function editPlan(id) {
    const plan = plans.find(p => p.id === id);
    if (!plan) return;

    // 수정 로직 구현
    // ...
}

function deletePlan(id) {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    fetch(`/delete_plan/${id}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                loadData();
            } else {
                alert('삭제 실패: ' + result.message);
            }
        });
}

function donePlan(id) {
    fetch(`/done_plan/${id}`, { method: 'POST' })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                loadData();
            } else {
                alert('완료 처리 실패: ' + result.message);
            }
        });
}

function undonePlan(id) {
    fetch(`/undone_plan/${id}`, { method: 'POST' })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                loadData();
            } else {
                alert('완료 취소 실패: ' + result.message);
            }
        });
}

// 데이터 로드
function loadData() {
    fetch('/plans')
        .then(res => res.json())
        .then(data => {
            plans = data.plans;
            renderTable();
            renderGantt();
            renderSummary();
        });
}

// 이벤트 리스너
window.addEventListener('resize', renderGantt);

// 제품명+BOM 조합에 대한 색상 생성 함수
function getColorForProduct(productName, bom) {
    const key = `${productName}-${bom}`;
    if (!colorMap[key]) {
        // 같은 제품명은 비슷한 색상 계열을 사용
        const existingProduct = Object.keys(colorMap).find(k => k.startsWith(productName + '-'));
        if (existingProduct) {
            // 기존 색상을 기반으로 약간 다른 색조 생성
            const baseColor = colorMap[existingProduct];
            const hslColor = rgbToHsl(hexToRgb(baseColor));
            hslColor.h = (hslColor.h + 0.1) % 1; // 색조만 약간 변경
            colorMap[key] = hslToHex(hslColor);
        } else {
            // 새로운 제품명이면 새로운 색상 할당
            const unusedColors = colors.filter(c => !Object.values(colorMap).includes(c));
            colorMap[key] = unusedColors.length > 0 ? unusedColors[0] : colors[Math.floor(Math.random() * colors.length)];
        }
    }
    return colorMap[key];
}

// 색상 변환 유틸리티 함수들
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function rgbToHsl(rgb) {
    let r = rgb.r / 255, g = rgb.g / 255, b = rgb.b / 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;

    if (max === min) {
        h = s = 0;
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case r: h = (g - b) / d + (g < b ? 6 : 0); break;
            case g: h = (b - r) / d + 2; break;
            case b: h = (r - g) / d + 4; break;
        }
        h /= 6;
    }
    return { h, s, l };
}

function hslToHex({ h, s, l }) {
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    const toHex = x => {
        const hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}
