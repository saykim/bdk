// 템플릿 정의
const templates = {
    flowchart: {
        name: '순서도',
        shapes: [
            { type: 'rect', x: 100, y: 100, width: 120, height: 60, text: '시작' },
            { type: 'diamond', x: 100, y: 200, width: 120, height: 120, text: '조건' },
            { type: 'rect', x: 100, y: 360, width: 120, height: 60, text: '처리' },
            { type: 'circle', x: 100, y: 460, width: 80, height: 80, text: '종료' }
        ],
        connections: [
            { start: { x: 160, y: 160 }, end: { x: 160, y: 200 } },
            { start: { x: 160, y: 320 }, end: { x: 160, y: 360 } },
            { start: { x: 160, y: 420 }, end: { x: 160, y: 460 } }
        ]
    },
    processMap: {
        name: '프로세스 맵',
        shapes: [
            { type: 'rect', x: 100, y: 100, width: 160, height: 60, text: '프로세스 1' },
            { type: 'rect', x: 300, y: 100, width: 160, height: 60, text: '프로세스 2' },
            { type: 'rect', x: 500, y: 100, width: 160, height: 60, text: '프로세스 3' }
        ],
        connections: [
            { start: { x: 260, y: 130 }, end: { x: 300, y: 130 } },
            { start: { x: 460, y: 130 }, end: { x: 500, y: 130 } }
        ]
    },
    swimlane: {
        name: '수영레인 다이어그램',
        shapes: [
            { type: 'rect', x: 100, y: 100, width: 800, height: 100, text: '부서 1', isLane: true },
            { type: 'rect', x: 100, y: 200, width: 800, height: 100, text: '부서 2', isLane: true },
            { type: 'rect', x: 100, y: 300, width: 800, height: 100, text: '부서 3', isLane: true }
        ]
    },
    mindmap: {
        name: '마인드맵',
        shapes: [
            { type: 'circle', x: 400, y: 200, width: 120, height: 120, text: '중심 주제' },
            { type: 'rect', x: 200, y: 100, width: 100, height: 40, text: '주제 1' },
            { type: 'rect', x: 200, y: 300, width: 100, height: 40, text: '주제 2' },
            { type: 'rect', x: 600, y: 100, width: 100, height: 40, text: '주제 3' },
            { type: 'rect', x: 600, y: 300, width: 100, height: 40, text: '주제 4' }
        ],
        connections: [
            { start: { x: 460, y: 200 }, end: { x: 300, y: 120 } },
            { start: { x: 460, y: 200 }, end: { x: 300, y: 320 } },
            { start: { x: 460, y: 200 }, end: { x: 600, y: 120 } },
            { start: { x: 460, y: 200 }, end: { x: 600, y: 320 } }
        ]
    }
};

class ProcessMap {
    constructor() {
        this.canvas = document.getElementById('canvas');
        if (!this.canvas) {
            console.error('Canvas element not found');
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.shapes = [];
        this.connections = [];
        this.selectedShape = null;
        this.selectedConnection = null;
        this.startConnector = null;
        this.tempConnection = null;
        
        // 상태 관리
        this.state = {
            mode: 'select',
            isDragging: false,
            isConnecting: false,
            startPoint: null,
            selectedItems: new Set()
        };
        
        // 기본 스타일
        this.defaultStyles = {
            shapeColor: '#3498db',
            textColor: '#2c3e50',
            lineStyle: 'solid',
            fontSize: '14px',
            lineWidth: 2
        };
        
        this.initializeEventListeners();
        this.resizeCanvas();
    }

    initializeEventListeners() {
        // 캔버스 이벤트
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // 도형 추가 버튼
        const shapeButtons = {
            'addRect': { type: 'rect', width: 120, height: 60 },
            'addCircle': { type: 'circle', width: 80, height: 80 },
            'addDiamond': { type: 'diamond', width: 100, height: 100 },
            'addParallelogram': { type: 'parallelogram', width: 120, height: 60 }
        };

        Object.entries(shapeButtons).forEach(([id, config]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', () => {
                    const center = this.getCanvasCenter();
                    this.addShape(config.type, center.x - config.width/2, center.y - config.height/2, config);
                });
            }
        });

        // 연결선 모드
        const connectionMode = document.getElementById('connectionMode');
        if (connectionMode) {
            connectionMode.addEventListener('click', () => {
                this.state.mode = this.state.mode === 'connect' ? 'select' : 'connect';
                connectionMode.classList.toggle('active');
            });
        }
    }

    addShape(type, x, y, config = {}) {
        const shape = {
            id: Date.now(),
            type: type,
            x: x,
            y: y,
            width: config.width || 120,
            height: config.height || 60,
            text: '새 도형',
            color: this.defaultStyles.shapeColor,
            textColor: this.defaultStyles.textColor,
            connectors: {}
        };
        
        this.updateShapeConnectors(shape);
        this.shapes.push(shape);
        this.selectedShape = shape;
        this.state.selectedItems.clear();
        this.state.selectedItems.add(shape);
        this.draw();
        
        return shape;
    }

    updateShapeConnectors(shape) {
        const { x, y, width, height } = shape;
        shape.connectors = {
            top: { x: x + width/2, y: y, type: 'top' },
            right: { x: x + width, y: y + height/2, type: 'right' },
            bottom: { x: x + width/2, y: y + height, type: 'bottom' },
            left: { x: x, y: y + height/2, type: 'left' }
        };
    }

    handleMouseDown(e) {
        const pos = this.getMousePosition(e);
        
        if (this.state.mode === 'connect') {
            const connector = this.findConnectorAtPosition(pos);
            if (connector) {
                this.state.isConnecting = true;
                this.startConnector = connector;
                this.tempConnection = {
                    start: connector,
                    end: { x: pos.x, y: pos.y }
                };
            }
        } else {
            const shape = this.findShapeAtPosition(pos.x, pos.y);
            if (shape) {
                if (!e.shiftKey) this.state.selectedItems.clear();
                this.state.selectedItems.add(shape);
                this.selectedShape = shape;
                this.state.isDragging = true;
                this.state.startPoint = pos;
            } else {
                this.state.selectedItems.clear();
                this.selectedShape = null;
            }
        }
        
        this.draw();
    }

    handleMouseMove(e) {
        const pos = this.getMousePosition(e);
        
        if (this.state.isConnecting && this.tempConnection) {
            this.tempConnection.end = pos;
        } else if (this.state.isDragging && this.selectedShape) {
            const dx = pos.x - this.state.startPoint.x;
            const dy = pos.y - this.state.startPoint.y;
            
            this.state.selectedItems.forEach(shape => {
                shape.x += dx;
                shape.y += dy;
                this.updateShapeConnectors(shape);
            });
            
            this.state.startPoint = pos;
        }
        
        this.draw();
    }

    handleMouseUp(e) {
        const pos = this.getMousePosition(e);
        
        if (this.state.isConnecting) {
            const connector = this.findConnectorAtPosition(pos);
            if (connector && connector !== this.startConnector) {
                this.connections.push({
                    id: Date.now(),
                    start: { ...this.startConnector },
                    end: { ...connector },
                    style: document.getElementById('connectionStyle').value || 'straight'
                });
            }
            this.state.isConnecting = false;
            this.startConnector = null;
            this.tempConnection = null;
        }
        
        this.state.isDragging = false;
        this.state.startPoint = null;
        
        this.draw();
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 연결선 그리기
        this.connections.forEach(conn => this.drawConnection(conn));
        
        // 임시 연결선 그리기
        if (this.tempConnection) {
            this.ctx.beginPath();
            this.ctx.strokeStyle = '#3498db';
            this.ctx.setLineDash([5, 5]);
            this.drawConnectionLine(this.tempConnection.start, this.tempConnection.end);
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }
        
        // 도형 그리기
        this.shapes.forEach(shape => {
            this.drawShape(shape);
            if (this.state.selectedItems.has(shape)) {
                this.drawShapeConnectors(shape);
            }
        });
    }

    drawShape(shape) {
        this.ctx.fillStyle = shape.color;
        this.ctx.strokeStyle = shape.color;
        this.ctx.lineWidth = 2;
        
        switch (shape.type) {
            case 'rect':
                this.ctx.beginPath();
                this.ctx.rect(shape.x, shape.y, shape.width, shape.height);
                break;
            case 'circle':
                this.ctx.beginPath();
                this.ctx.ellipse(
                    shape.x + shape.width/2,
                    shape.y + shape.height/2,
                    shape.width/2,
                    shape.height/2,
                    0, 0, Math.PI * 2
                );
                break;
            case 'diamond':
                this.ctx.beginPath();
                this.ctx.moveTo(shape.x + shape.width/2, shape.y);
                this.ctx.lineTo(shape.x + shape.width, shape.y + shape.height/2);
                this.ctx.lineTo(shape.x + shape.width/2, shape.y + shape.height);
                this.ctx.lineTo(shape.x, shape.y + shape.height/2);
                this.ctx.closePath();
                break;
            case 'parallelogram':
                const offset = shape.width * 0.2;
                this.ctx.beginPath();
                this.ctx.moveTo(shape.x + offset, shape.y);
                this.ctx.lineTo(shape.x + shape.width, shape.y);
                this.ctx.lineTo(shape.x + shape.width - offset, shape.y + shape.height);
                this.ctx.lineTo(shape.x, shape.y + shape.height);
                this.ctx.closePath();
                break;
        }
        
        this.ctx.fill();
        this.ctx.stroke();
        
        // 텍스트 그리기
        this.ctx.fillStyle = shape.textColor;
        this.ctx.font = `${shape.fontSize || '14px'} Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(
            shape.text,
            shape.x + shape.width/2,
            shape.y + shape.height/2
        );
    }

    drawConnection(conn) {
        this.ctx.beginPath();
        this.ctx.strokeStyle = '#3498db';
        this.ctx.lineWidth = 2;
        
        this.drawConnectionLine(conn.start, conn.end, conn.style);
        
        this.ctx.stroke();
        this.drawArrowhead(conn.end.x, conn.end.y, this.calculateAngle(conn.start, conn.end));
    }

    drawConnectionLine(start, end, style = 'straight') {
        switch (style) {
            case 'orthogonal':
                const midX = (start.x + end.x) / 2;
                this.ctx.moveTo(start.x, start.y);
                this.ctx.lineTo(midX, start.y);
                this.ctx.lineTo(midX, end.y);
                this.ctx.lineTo(end.x, end.y);
                break;
            case 'curved':
                const cp1x = start.x + (end.x - start.x) / 3;
                const cp1y = start.y;
                const cp2x = start.x + (end.x - start.x) * 2/3;
                const cp2y = end.y;
                this.ctx.moveTo(start.x, start.y);
                this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, end.x, end.y);
                break;
            default: // straight
                this.ctx.moveTo(start.x, start.y);
                this.ctx.lineTo(end.x, end.y);
        }
    }

    drawArrowhead(x, y, angle) {
        const size = 10;
        
        this.ctx.save();
        this.ctx.translate(x, y);
        this.ctx.rotate(angle);
        
        this.ctx.beginPath();
        this.ctx.moveTo(-size, -size/2);
        this.ctx.lineTo(0, 0);
        this.ctx.lineTo(-size, size/2);
        
        this.ctx.stroke();
        this.ctx.restore();
    }

    drawShapeConnectors(shape) {
        Object.values(shape.connectors).forEach(connector => {
            this.ctx.beginPath();
            this.ctx.arc(connector.x, connector.y, 5, 0, Math.PI * 2);
            this.ctx.fillStyle = '#3498db';
            this.ctx.fill();
        });
    }

    getMousePosition(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    findShapeAtPosition(x, y) {
        return this.shapes.find(shape => {
            return x >= shape.x && x <= shape.x + shape.width &&
                   y >= shape.y && y <= shape.y + shape.height;
        });
    }

    findConnectorAtPosition(pos) {
        const radius = 5;
        for (const shape of this.shapes) {
            for (const connector of Object.values(shape.connectors)) {
                const dx = pos.x - connector.x;
                const dy = pos.y - connector.y;
                if (Math.sqrt(dx * dx + dy * dy) <= radius) {
                    return connector;
                }
            }
        }
        return null;
    }

    calculateAngle(start, end) {
        return Math.atan2(end.y - start.y, end.x - start.x);
    }

    getCanvasCenter() {
        return {
            x: this.canvas.width / 2,
            y: this.canvas.height / 2
        };
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.draw();
    }
}

// 전역 인스턴스 생성
document.addEventListener('DOMContentLoaded', () => {
    window.processMap = new ProcessMap();
});

async function loadDiagramList() {
    try {
        const response = await fetch('/api/list_diagrams');
        const result = await response.json();
        
        if (result.success) {
            const listElement = document.getElementById('diagramList');
            listElement.innerHTML = '';
            
            result.diagrams.forEach(diagram => {
                const li = document.createElement('li');
                li.textContent = diagram.name;
                li.addEventListener('click', () => loadDiagram(diagram.name));
                listElement.appendChild(li);
            });
        }
    } catch (error) {
        showNotification('다이어그램 목록을 불러오는데 실패했습니다.', true);
    }
}

async function loadDiagram(name) {
    try {
        const response = await fetch(`/api/load_diagram?name=${encodeURIComponent(name)}`);
        const result = await response.json();
        
        if (result.success) {
            processMap.fromJSON(JSON.parse(result.data));
            document.getElementById('diagramName').value = name;
            showNotification('다이어그램을 불러왔습니다.');
        } else {
            showNotification('다이어그램을 찾을 수 없습니다.', true);
        }
    } catch (error) {
        showNotification('다이어그램을 불러오는데 실패했습니다.', true);
    }
}

function showNotification(message, isError = false) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification${isError ? ' error' : ''}`;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
} 