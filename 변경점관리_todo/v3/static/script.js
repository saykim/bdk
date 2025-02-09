// 날짜 입력 필드의 기본값을 오늘로 설정
document.addEventListener('DOMContentLoaded', function() {
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    
    if (startDateInput && endDateInput) {
        const today = new Date().toISOString().split('T')[0];
        startDateInput.value = today;
        endDateInput.value = today;
        
        // 종료일이 시작일보다 이전이 되지 않도록 설정
        startDateInput.addEventListener('change', function() {
            if (endDateInput.value < startDateInput.value) {
                endDateInput.value = startDateInput.value;
            }
            endDateInput.min = startDateInput.value;
        });
        
        endDateInput.min = today;
    }

    // 캘린더 초기화
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            locale: 'ko',
            events: generateEvents(),
            eventClick: function(info) {
                // 작업 상세 정보를 표시하는 기능을 추가할 수 있습니다
                alert(info.event.title);
            }
        });
        calendar.render();
    }
});

// 작업 목록에서 이벤트 생성
function generateEvents() {
    const events = [];
    const rows = document.querySelectorAll('table tbody tr');
    
    rows.forEach(row => {
        const startDate = row.dataset.start;
        const endDate = row.dataset.end;
        const orderNumber = row.querySelector('td:first-child').textContent;
        const workOrder = row.querySelector('td:nth-child(2)').textContent;
        const status = row.querySelector('.status-select').value;
        
        let backgroundColor;
        switch (status) {
            case 'pending':
                backgroundColor = '#ffc107';
                break;
            case 'in_progress':
                backgroundColor = '#007bff';
                break;
            case 'completed':
                backgroundColor = '#28a745';
                break;
            default:
                backgroundColor = '#6c757d';
        }
        
        events.push({
            title: `[${orderNumber}] ${workOrder}`,
            start: startDate,
            end: endDate,
            backgroundColor: backgroundColor,
            borderColor: backgroundColor
        });
    });
    
    return events;
}

// 작업 상태 업데이트
function updateStatus(selectElement) {
    const taskId = selectElement.dataset.taskId;
    const newStatus = selectElement.value;
    
    fetch(`/task/${taskId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `status=${newStatus}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 상태 업데이트 성공 시 배경색 변경
            const row = selectElement.closest('tr');
            row.style.backgroundColor = '#e8f5e9';
            setTimeout(() => {
                row.style.backgroundColor = '';
                // 캘린더 이벤트 업데이트
                const calendarEl = document.getElementById('calendar');
                if (calendarEl) {
                    const calendar = calendarEl.fullCalendar;
                    if (calendar) {
                        calendar.refetchEvents();
                    }
                }
            }, 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('상태 업데이트에 실패했습니다.');
    });
} 