// 인증 상태 확인
function checkAuth() {
    const token = localStorage.getItem('token');
    const currentPath = window.location.pathname;
    
    // 로그인이 필요한 페이지에서 토큰이 없는 경우
    if (!token && currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = '/login';
        return false;
    }
    
    // 이미 로그인된 상태에서 로그인/회원가입 페이지 접근 시
    if (token && (currentPath === '/login' || currentPath === '/register')) {
        window.location.href = '/';
        return false;
    }
    
    return true;
}

// 로그아웃 함수
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// 작업 우선순위에 따른 클래스 반환
function getPriorityClass(priority) {
    switch(priority) {
        case 2:
            return 'priority-high';
        case 1:
            return 'priority-medium';
        default:
            return 'priority-low';
    }
}

// 날짜 포맷팅
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// API 요청 헬퍼 함수
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        if (response.status === 401) {
            logout();
            return null;
        }
        return response;
    } catch (error) {
        console.error('API request failed:', error);
        return null;
    }
}

// 작업 정렬 함수
function sortTasks(tasks, sortBy) {
    return tasks.sort((a, b) => {
        switch(sortBy) {
            case 'priority':
                return b.priority - a.priority;
            case 'dueDate':
                if (!a.due_date) return 1;
                if (!b.due_date) return -1;
                return new Date(a.due_date) - new Date(b.due_date);
            case 'name':
                return a.name.localeCompare(b.name);
            default:
                return 0;
        }
    });
}

// 페이지 로드 시 인증 확인
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
}); 