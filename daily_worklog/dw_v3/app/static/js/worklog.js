// Flatpickr 설정
function initializeFlatpickr() {
    flatpickr.localize(flatpickr.l10ns.ko);
    const commonConfig = {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        minuteIncrement: 1
    };

    flatpickr("#work_start_time", {
        ...commonConfig,
        onChange: function(selectedDates) {
            const endPicker = document.querySelector("#work_end_time")._flatpickr;
            endPicker.set("minDate", selectedDates[0]);
        }
    });

    flatpickr("#work_end_time", {
        ...commonConfig,
        onChange: function(selectedDates) {
            const startPicker = document.querySelector("#work_start_time")._flatpickr;
            startPicker.set("maxDate", selectedDates[0]);
        }
    });
}

// 작업 일지 목록 로드
async function loadWorklogs() {
    try {
        const response = await fetch('/api/worklogs');
        if (!response.ok) throw new Error('작업 일지 로드 실패');
        
        const worklogs = await response.json();
        const tbody = document.getElementById('worklogTableBody');
        tbody.innerHTML = '';

        worklogs.forEach(worklog => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${worklog.product_name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${worklog.order_number}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${formatDateTime(worklog.work_start_time)} ~ 
                    ${formatDateTime(worklog.work_end_time)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${worklog.quantity_produced} ${worklog.unit}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${worklog.quality_check ? '✅' : '❌'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${worklog.user_name || '알 수 없음'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${formatDateTime(worklog.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="editWorklog(${worklog.id})" class="btn-edit mr-2">수정</button>
                    <button onclick="deleteWorklog(${worklog.id})" class="btn-delete">삭제</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        showNotification('작업 일지 로드 중 오류가 발생했습니다.', 'error');
        console.error('작업 일지 로드 중 오류 발생:', error);
    }
}

// 작업 일지 저장
async function saveWorklog(formData) {
    try {
        const response = await fetch('/api/worklogs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '저장 실패');
        }

        showNotification('작업 일지가 성공적으로 저장되었습니다.', 'success');
        document.getElementById('worklogForm').reset();
        await loadWorklogs();
    } catch (error) {
        showNotification(error.message, 'error');
        console.error('작업 일지 저장 중 오류 발생:', error);
    }
}

// 작업 일지 삭제
async function deleteWorklog(id) {
    if (!confirm('정말로 이 작업 일지를 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await fetch(`/api/worklogs/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '삭제 실패');
        }

        showNotification('작업 일지가 성공적으로 삭제되었습니다.', 'success');
        await loadWorklogs();
    } catch (error) {
        showNotification(error.message, 'error');
        console.error('작업 일지 삭제 중 오류 발생:', error);
    }
}

// 유틸리티 함수
function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.textContent = message;
    
    const container = document.querySelector('.notification-container');
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 이벤트 리스너
document.addEventListener('DOMContentLoaded', () => {
    initializeFlatpickr();
    loadWorklogs();

    // 폼 제출 이벤트 처리
    document.getElementById('worklogForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            product_name: document.getElementById('product_name').value,
            order_number: document.getElementById('order_number').value,
            work_start_time: document.getElementById('work_start_time').value,
            work_end_time: document.getElementById('work_end_time').value,
            quantity_produced: document.getElementById('quantity_produced').value,
            unit: document.getElementById('unit').value,
            temperature: document.getElementById('temperature').value || 0,
            humidity: document.getElementById('humidity').value || 0,
            quality_check: document.getElementById('quality_check').checked,
            notes: document.getElementById('notes').value
        };

        await saveWorklog(formData);
    });
}); 