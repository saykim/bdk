let gantt = null;

// 간트 차트 초기화 및 데이터 로드
async function initGantt() {
    try {
        const response = await fetch('/api/orders');
        const orders = await response.json();
        
        const tasks = orders.map(order => ({
            id: order.id,
            name: `${order.factory} - ${order.product} (${order.order_no})`,
            start: order.start_time,
            end: order.end_time,
            progress: 100,
            custom_class: `status-${order.status}`
        }));
        
        if (gantt) {
            document.querySelector('#gantt').innerHTML = '';
        }
        
        gantt = new Gantt("#gantt", tasks, {
            view_modes: ['Quarter Day', 'Half Day', 'Day', 'Week', 'Month'],
            view_mode: 'Day',
            date_format: 'YYYY-MM-DD HH:mm',
            popup_trigger: 'mouseover',  // 마우스 오버시에만 툴팁 표시
            custom_popup_html: function(task) {
                const order = orders.find(o => o.id === task.id);
                return `
                    <div class="bg-white p-2 rounded shadow-lg">
                        <div class="font-bold">${order.factory} - ${order.product}</div>
                        <div>오더번호: ${order.order_no}</div>
                        <div>수량: ${order.quantity.toLocaleString()}</div>
                        <div>상태: ${order.status}</div>
                        <div>시작: ${order.start_time}</div>
                        <div>종료: ${order.end_time}</div>
                    </div>
                `;
            },
            on_date_change: function(task, start, end) {
                updateOrderDates(task.id, start, end);
            },
            on_click: function(task) {
                console.log("Task clicked:", task);
            }
        });

        // 툴팁 마우스 아웃 이벤트 처리
        const ganttContainer = document.querySelector('.gantt-container');
        const bars = ganttContainer.querySelectorAll('.bar-wrapper');
        
        bars.forEach(bar => {
            bar.addEventListener('mouseleave', () => {
                const popup = ganttContainer.querySelector('.popup-wrapper');
                if (popup) {
                    popup.style.opacity = '0';
                    setTimeout(() => {
                        if (popup.parentNode) {
                            popup.parentNode.removeChild(popup);
                        }
                    }, 200);
                }
            });
        });

    } catch (error) {
        console.error('간트 차트 초기화 중 오류 발생:', error);
        alert('데이터 로드 중 오류가 발생했습니다.');
    }
}

// 생산오더 생성
async function createOrder() {
    try {
        const data = {
            factory: document.getElementById('factory').value,
            product: document.getElementById('product').value,
            order_no: document.getElementById('order_no').value,
            quantity: document.getElementById('quantity').value,
            start_time: document.getElementById('start_time').value.replace('T', ' '),
            end_time: document.getElementById('end_time').value.replace('T', ' '),
            status: document.getElementById('status').value
        };

        // 입력 검증
        if (!validateOrderInput(data)) {
            return;
        }
        
        const response = await fetch('/api/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('생산오더가 등록되었습니다.');
            resetForm();
            initGantt();
        } else {
            const error = await response.json();
            alert(error.message || '생산오더 등록에 실패했습니다.');
        }
    } catch (error) {
        console.error('생산오더 생성 중 오류 발생:', error);
        alert('생산오더 등록 중 오류가 발생했습니다.');
    }
}

// 입력 폼 검증
function validateOrderInput(data) {
    if (!data.factory || !data.product || !data.order_no || !data.quantity || !data.start_time || !data.end_time) {
        alert('모든 필드를 입력해주세요.');
        return false;
    }
    
    if (isNaN(data.quantity) || data.quantity <= 0) {
        alert('수량은 0보다 큰 숫자여야 합니다.');
        return false;
    }
    
    const start = new Date(data.start_time);
    const end = new Date(data.end_time);
    if (end <= start) {
        alert('종료시간은 시작시간보다 늦어야 합니다.');
        return false;
    }
    
    return true;
}

// 폼 초기화
function resetForm() {
    document.getElementById('factory').value = '';
    document.getElementById('product').value = '';
    document.getElementById('order_no').value = '';
    document.getElementById('quantity').value = '';
    document.getElementById('start_time').value = '';
    document.getElementById('end_time').value = '';
    document.getElementById('status').value = '계획';
}

// 날짜 변경 시 서버 업데이트
async function updateOrderDates(orderId, start, end) {
    try {
        const startStr = formatDateTime(start);
        const endStr = formatDateTime(end);
        
        const response = await fetch(`/api/orders/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_time: startStr,
                end_time: endStr,
                status: '변경'
            })
        });
        
        if (response.ok) {
            initGantt();
        } else {
            const error = await response.json();
            alert(error.message || '일정 변경에 실패했습니다.');
        }
    } catch (error) {
        console.error('일정 업데이트 중 오류 발생:', error);
        alert('일정 변경 중 오류가 발생했습니다.');
    }
}

// 날짜 포맷 변환
function formatDateTime(date) {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hour = String(d.getHours()).padStart(2, '0');
    const minute = String(Math.floor(d.getMinutes() / 10) * 10).padStart(2, '0');
    return `${year}-${month}-${day} ${hour}:${minute}`;
}

// 뷰 모드 변경
function updateViewMode() {
    const mode = document.getElementById('viewMode').value;
    gantt.change_view_mode(mode);
}

// PDF 출력
function exportPDF() {
    window.location.href = '/api/export/pdf';
}

// Excel 출력
function exportExcel() {
    window.location.href = '/api/export/excel';
}

// 초기 로드
document.addEventListener('DOMContentLoaded', initGantt); 