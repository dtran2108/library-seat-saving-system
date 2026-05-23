// 座位坐標映射（基於 plazaA.jpg 的百分比位置）
// 格式: { deskNo: 'A-01', x: %, y: %, r: % }
const PLAZA_A_SEATS = [
    // Row 1 (上排左側)
    { deskNo: 'A-01', x: 7, y: 92, r: 4 },
    { deskNo: 'A-02', x: 7, y: 78, r: 4 },
    { deskNo: 'A-03', x: 7, y: 64, r: 4 },
    { deskNo: 'A-04', x: 7, y: 50, r: 4 },
    { deskNo: 'A-05', x: 7, y: 36, r: 4 },
    { deskNo: 'A-06', x: 7, y: 22, r: 4 },
    { deskNo: 'A-07', x: 7, y: 8, r: 4 },
    
    // Row 2
    { deskNo: 'A-08', x: 15, y: 92, r: 4 },
    { deskNo: 'A-09', x: 15, y: 78, r: 4 },
    { deskNo: 'A-10', x: 15, y: 64, r: 4 },
    { deskNo: 'A-11', x: 15, y: 50, r: 4 },
    { deskNo: 'A-12', x: 15, y: 36, r: 4 },
    { deskNo: 'A-13', x: 15, y: 22, r: 4 },
    { deskNo: 'A-14', x: 15, y: 8, r: 4 },
    
    // Row 3
    { deskNo: 'A-15', x: 23, y: 92, r: 4 },
    { deskNo: 'A-16', x: 23, y: 78, r: 4 },
    { deskNo: 'A-17', x: 23, y: 64, r: 4 },
    { deskNo: 'A-18', x: 23, y: 50, r: 4 },
    { deskNo: 'A-19', x: 23, y: 36, r: 4 },
    { deskNo: 'A-20', x: 23, y: 22, r: 4 },
    { deskNo: 'A-21', x: 23, y: 8, r: 4 },
    
    // Row 4
    { deskNo: 'A-22', x: 31, y: 92, r: 4 },
    { deskNo: 'A-23', x: 31, y: 78, r: 4 },
    { deskNo: 'A-24', x: 31, y: 64, r: 4 },
    { deskNo: 'A-25', x: 31, y: 50, r: 4 },
    { deskNo: 'A-26', x: 31, y: 36, r: 4 },
    { deskNo: 'A-27', x: 31, y: 22, r: 4 },
    { deskNo: 'A-28', x: 31, y: 8, r: 4 },
    
    // Row 5
    { deskNo: 'A-29', x: 45, y: 92, r: 4 },
    { deskNo: 'A-30', x: 45, y: 78, r: 4 },
    { deskNo: 'A-31', x: 45, y: 64, r: 4 },
    { deskNo: 'A-32', x: 45, y: 50, r: 4 },
    { deskNo: 'A-33', x: 45, y: 36, r: 4 },
    { deskNo: 'A-34', x: 45, y: 22, r: 4 },
    { deskNo: 'A-35', x: 45, y: 8, r: 4 },
    
    // Row 6
    { deskNo: 'A-36', x: 59, y: 92, r: 4 },
    { deskNo: 'A-37', x: 59, y: 78, r: 4 },
    { deskNo: 'A-38', x: 59, y: 64, r: 4 },
    { deskNo: 'A-39', x: 59, y: 50, r: 4 },
    { deskNo: 'A-40', x: 59, y: 36, r: 4 },
    { deskNo: 'A-41', x: 59, y: 22, r: 4 },
    { deskNo: 'A-42', x: 59, y: 8, r: 4 },
    
    // Row 7
    { deskNo: 'A-43', x: 73, y: 92, r: 4 },
    { deskNo: 'A-44', x: 73, y: 78, r: 4 },
    { deskNo: 'A-45', x: 73, y: 64, r: 4 },
    { deskNo: 'A-46', x: 73, y: 50, r: 4 },
    { deskNo: 'A-47', x: 73, y: 36, r: 4 },
    { deskNo: 'A-48', x: 73, y: 22, r: 4 },
    { deskNo: 'A-49', x: 73, y: 8, r: 4 }
];

// 根據座位狀態返回顏色
function getSeatColor(status) {
    if (status === 'occupied') return '#fca5a5'; // 紅色
    if (status === 'blocked') return '#d1d5db'; // 灰色
    return '#86efac'; // 綠色
}

// 根據座位狀態返回邊框顏色
function getSeatBorderColor(status) {
    if (status === 'occupied') return '#dc2626'; // 深紅
    if (status === 'blocked') return '#6b7280'; // 深灰
    return '#22c55e'; // 深綠
}

// 初始化 SVG overlay
function initSeatOverlay(zoneId, seats) {
    // 查找父級卡片
    const zoneCard = document.querySelector(`.zone-card[data-zone-id="${zoneId}"]`);
    if (!zoneCard) {
        console.warn(`Zone card not found for zoneId: ${zoneId}`);
        return;
    }
    
    const container = zoneCard.querySelector('.plaza-image-container');
    if (!container) {
        console.warn(`Image container not found in zone card ${zoneId}`);
        return;
    }
    
    const img = container.querySelector('img');
    if (!img) {
        console.warn(`Image not found in container for zone ${zoneId}`);
        return;
    }
    
    // 如果已經有 SVG，先移除
    const existingSvg = container.querySelector('.plaza-seat-overlay');
    if (existingSvg) {
        existingSvg.remove();
    }
    
    // 建立座位狀態 Map
    const seatMap = new Map(seats.map(s => [s.deskNo, s]));
    
    // 建立 SVG overlay
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'plaza-seat-overlay');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    
    // 為每個座位建立圓形
    PLAZA_A_SEATS.forEach(seatCoord => {
        const seat = seatMap.get(seatCoord.deskNo);
        const status = seat ? seat.status : 'available';
        const seatId = seat ? seat.seatId : null;
        
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', seatCoord.x);
        circle.setAttribute('cy', seatCoord.y);
        circle.setAttribute('r', seatCoord.r);
        circle.setAttribute('fill', getSeatColor(status));
        circle.setAttribute('stroke', getSeatBorderColor(status));
        circle.setAttribute('stroke-width', '0.3');
        circle.setAttribute('class', `seat-circle seat-${status}`);
        circle.setAttribute('data-desk-no', seatCoord.deskNo);
        circle.setAttribute('data-seat-id', seatId || '');
        circle.setAttribute('data-status', status);
        
        // 添加文字標籤
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', seatCoord.x);
        text.setAttribute('y', seatCoord.y);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('dominant-baseline', 'middle');
        text.setAttribute('font-size', '1.5');
        text.setAttribute('font-weight', 'bold');
        text.setAttribute('class', 'seat-text');
        text.setAttribute('pointer-events', 'none');
        
        if (status === 'occupied') {
            text.setAttribute('fill', '#991b1b');
        } else if (status === 'blocked') {
            text.setAttribute('fill', '#4b5563');
        } else {
            text.setAttribute('fill', '#16a34a');
        }
        
        text.textContent = seatCoord.deskNo.replace('A-', 'A');
        
        // 添加點擊事件
        if (status === 'available' && seatId) {
            circle.style.cursor = 'pointer';
            circle.addEventListener('click', () => {
                const deskNo = seatCoord.deskNo;
                const seatLabel = `Learning Plaza A · ${deskNo}`;
                openBookingModal(seatId, seatLabel);
            });
            
            // 懸停效果
            circle.addEventListener('mouseenter', () => {
                circle.setAttribute('r', seatCoord.r + 0.5);
                circle.style.filter = 'drop-shadow(0 0 0.5px rgba(34, 197, 94, 0.6))';
            });
            circle.addEventListener('mouseleave', () => {
                circle.setAttribute('r', seatCoord.r);
                circle.style.filter = 'none';
            });
        }
        
        svg.appendChild(circle);
        svg.appendChild(text);
    });
    
    // 將 SVG 插入到容器
    container.appendChild(svg);
    console.log(`SVG overlay initialized for zone ${zoneId} with ${PLAZA_A_SEATS.length} seats`);
}
