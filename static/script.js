document.addEventListener('DOMContentLoaded', () => {
    // Check if we need to login by trying to query (auto-detect week)
    // Or just simple: if we get 401 on query, show login.
    // But user wants popup on open. Let's try a lightweight check or just query.
    queryData(true); // true = isInitialLoad

    // Setup Login Form
    const loginForm = document.getElementById('loginForm');
    loginForm.addEventListener('submit', handleLogin);
});

async function handleLogin(e) {
    e.preventDefault();
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('loginError');

    const username = usernameInput.value;
    const password = passwordInput.value;

    // Loading state
    loginBtn.disabled = true;
    loginBtn.innerText = '登录中...';
    errorDiv.classList.add('hidden');

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            // If 404 (backend not found), treat as demo mode restriction
            if (response.status === 404 || response.status === 405) {
                throw new Error('演示模式下无法登录');
            }
            const data = await response.json();
            throw new Error(data.detail || '登录失败');
        }

        // Success
        hideLoginModal();
        // Trigger query after login
        queryData();

    } catch (error) {
        // If fetch failed completely (network error), also demo mode
        if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
            errorDiv.innerText = '演示模式下无法登录 (后端未连接)';
        } else {
            errorDiv.innerText = error.message;
        }
        errorDiv.classList.remove('hidden');
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerText = '登录';
    }
}

function showLoginModal() {
    const modal = document.getElementById('loginModal');
    const content = document.getElementById('loginContent');
    modal.classList.remove('hidden');
    // Trigger reflow
    void modal.offsetWidth;
    modal.classList.remove('opacity-0');
    content.classList.remove('scale-95');
    content.classList.add('scale-100');
}

function hideLoginModal() {
    const modal = document.getElementById('loginModal');
    const content = document.getElementById('loginContent');
    modal.classList.add('opacity-0');
    content.classList.remove('scale-100');
    content.classList.add('scale-95');

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

// Help Modal Logic
function showHelpModal() {
    const modal = document.getElementById('helpModal');
    const content = document.getElementById('helpContent');
    modal.classList.remove('hidden');
    // Trigger reflow
    void modal.offsetWidth;
    modal.classList.remove('opacity-0');
    content.classList.remove('scale-95');
    content.classList.add('scale-100');
}

function hideHelpModal() {
    const modal = document.getElementById('helpModal');
    const content = document.getElementById('helpContent');
    modal.classList.add('opacity-0');
    content.classList.remove('scale-100');
    content.classList.add('scale-95');

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

async function queryData(isInitialLoad = false) {
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

    // If initial load, don't show main loading spinner yet, just try silently?
    // Or show it.
    if (!isInitialLoad) {
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
    }

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (response.status === 401) {
            // Need login
            showLoginModal();
            if (!isInitialLoad) {
                loading.classList.add('hidden');
                queryBtn.disabled = false;
                queryBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                queryBtn.innerText = '查询';
            }
            return;
        }

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.warn('API Request failed, trying mock data...', error);

        // Fallback to mock data for GitHub Pages or when backend is down
        try {
            const mockResponse = await fetch('mock_data.json');
            if (mockResponse.ok) {
                const mockData = await mockResponse.json();

                // Show a toast or message indicating demo mode
                if (!isInitialLoad) {
                    const errorDiv = document.getElementById('error');
                    errorDiv.classList.remove('hidden');
                    errorDiv.innerHTML = '<span class="text-orange-500">注意：后端服务不可用，当前显示演示数据。</span>';
                }

                displayResults(mockData);
            } else {
                throw new Error('Mock data not found');
            }
        } catch (mockError) {
            console.error('Mock data failed:', mockError);
            if (!isInitialLoad) {
                errorDiv.classList.remove('hidden');
                errorDiv.innerText = '查询出错: ' + error.message;
            }
        }
    } finally {
        if (!isInitialLoad) {
            loading.classList.add('hidden');
            queryBtn.disabled = false;
            queryBtn.classList.remove('opacity-75', 'cursor-not-allowed');
            queryBtn.innerText = '查询';
        }
    }
}

function displayResults(data) {
    const container = document.getElementById('results');
    container.innerHTML = ''; // Clear previous

    // data structure: { week: 10, buildings: [...] }
    const buildings = data.buildings;
    const week = data.week;

    if (!buildings || buildings.length === 0) {
        container.innerHTML = '<div class="col-span-full text-center text-gray-400 py-12">未找到数据</div>';
    } else {
        // Add a header for the week
        const weekHeader = document.createElement('div');
        weekHeader.className = 'col-span-full text-center mb-8';
        weekHeader.innerHTML = `
            <span class="inline-block bg-black text-white text-sm font-bold px-4 py-2 rounded-full mb-2">第 ${week} 周</span>
            <h2 class="text-2xl font-bold">查询结果</h2>
        `;
        container.appendChild(weekHeader);

        buildings.forEach(item => {
            const card = document.createElement('div');
            // New Card Style: White, large rounded, subtle border
            card.className = 'bg-white border border-gray-100 rounded-[2rem] p-8 flex flex-col shadow-sm hover:shadow-xl transition-all duration-300 group';

            const buildingTitle = document.createElement('h3');
            buildingTitle.className = 'text-xl font-bold text-black mb-6 flex items-center';
            // Minimal dot indicator
            buildingTitle.innerHTML = `<span class="w-2 h-2 bg-black rounded-full mr-3"></span>${item.building}`;

            const roomInfo = document.createElement('div');
            roomInfo.className = 'flex-1 flex flex-col justify-between';

            const bestRoom = item.best_room;

            roomInfo.innerHTML = `
                <div class="mb-6">
                    <p class="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-2">推荐教室</p>
                    <p class="text-4xl font-bold text-black tracking-tight">${bestRoom.room}</p>
                </div>
                
                <div class="bg-gray-50 rounded-2xl p-5">
                    <div class="flex justify-between items-end mb-3">
                        <span class="text-gray-500 text-sm font-medium">连续空闲</span>
                        <span class="text-2xl font-bold text-black">${bestRoom.max_free} <span class="text-sm text-gray-400 font-normal">节</span></span>
                    </div>
                    <!-- Progress Bar: Black fill -->
                    <div class="w-full bg-gray-200 rounded-full h-2 mb-3 overflow-hidden">
                        <div class="bg-black h-2 rounded-full transition-all duration-1000 ease-out" style="width: ${Math.min((bestRoom.max_free / 7) * 100, 100)}%"></div>
                    </div>
                    <p class="text-sm text-gray-600 font-medium">${bestRoom.time_range}</p>
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
