async function queryData() {
    const weekInput = document.getElementById('weekInput');
    const queryBtn = document.getElementById('queryBtn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results');
    const errorDiv = document.getElementById('error');

    const weekVal = weekInput.value;
    const payload = {};
    if (weekVal) {
        payload.week = parseInt(weekVal);
    }

    // Reset UI
    resultsContainer.innerHTML = '';
    resultsContainer.classList.add('hidden');
    resultsContainer.classList.remove('opacity-100');
    errorDiv.classList.add('hidden');

    // Loading State
    loading.classList.remove('hidden');
    queryBtn.disabled = true;
    queryBtn.classList.add('opacity-75', 'cursor-not-allowed');
    queryBtn.innerText = '查询中...';

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        errorDiv.classList.remove('hidden');
        errorDiv.innerText = '查询出错: ' + error.message;
    } finally {
        loading.classList.add('hidden');
        queryBtn.disabled = false;
        queryBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        queryBtn.innerText = '查询';
    }
}

function displayResults(data) {
    const container = document.getElementById('results');

    // data structure: { week: 10, buildings: [...] }
    const buildings = data.buildings;
    const week = data.week;

    // Update header or show week info if needed
    // For now just show results

    if (!buildings || buildings.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-400">未找到数据</div>';
    } else {
        // Add a header for the week
        const weekHeader = document.createElement('div');
        weekHeader.className = 'col-span-full text-center text-2xl font-bold text-blue-400 mb-4';
        weekHeader.innerText = `第 ${week} 周查询结果`;
        container.appendChild(weekHeader);

        buildings.forEach(item => {
            const card = document.createElement('div');
            card.className = 'glass-card rounded-2xl p-6 flex flex-col relative overflow-hidden group';

            // Gradient border effect at top
            const borderTop = document.createElement('div');
            borderTop.className = 'absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left';
            card.appendChild(borderTop);

            const buildingTitle = document.createElement('h3');
            buildingTitle.className = 'text-xl font-bold text-gray-100 mb-4 flex items-center';
            buildingTitle.innerHTML = `<span class="w-2 h-8 bg-blue-500 rounded-full mr-3"></span>${item.building}`;

            const roomInfo = document.createElement('div');
            roomInfo.className = 'flex-1';

            const bestRoom = item.best_room;

            roomInfo.innerHTML = `
                <div class="mb-4">
                    <p class="text-sm text-gray-400 uppercase tracking-wider mb-1">推荐教室</p>
                    <p class="text-3xl font-bold text-blue-400">${bestRoom.room}</p>
                </div>
                
                <div class="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                    <div class="flex justify-between items-end mb-2">
                        <span class="text-gray-400 text-sm">连续空闲</span>
                        <span class="text-2xl font-bold text-white">${bestRoom.max_free} <span class="text-sm text-gray-500 font-normal">节</span></span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2 mb-3">
                        <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style="width: ${Math.min((bestRoom.max_free / 14) * 100, 100)}%"></div>
                    </div>
                    <p class="text-sm text-gray-300 font-medium">${bestRoom.time_range}</p>
                </div>
            `;

            card.appendChild(buildingTitle);
            card.appendChild(roomInfo);
            container.appendChild(card);
        });
    }

    container.classList.remove('hidden');
    // Trigger reflow for transition
    void container.offsetWidth;
    container.classList.add('opacity-100');
}
