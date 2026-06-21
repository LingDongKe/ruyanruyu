// ============================================
// 全局状态
// ============================================
let currentMode = 'char';
let lastQuery = '';

// ============================================
// DOM 元素
// ============================================
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const modeChar = document.getElementById('modeChar');
const modeMeaning = document.getElementById('modeMeaning');
const resultHeader = document.getElementById('resultHeader');
const resultInfo = document.getElementById('resultInfo');
const resultMode = document.getElementById('resultMode');
const resultBody = document.getElementById('resultBody');
const emptyState = document.getElementById('emptyState');

// ============================================
// API 调用
// ============================================
const API_BASE = '/api';

async function search(query, mode) {
    if (!query || !query.trim()) {
        showEmptyState('请输入搜索内容');
        return;
    }

    const queryKey = `${query}_${mode}`;
    if (queryKey === lastQuery) {
        return;
    }
    lastQuery = queryKey;

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&mode=${mode}`);
        const result = await response.json();

        if (result.success) {
            renderResults(result);
        } else {
            showEmptyState(result.message || '查询失败，请重试');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        showEmptyState('网络连接失败，请检查服务是否正常运行');
    }
}

// ============================================
// 渲染结果 - 按输入顺序显示
// ============================================
function renderResults(result) {
    const { data, order, total_count, mode_name } = result;

    emptyState.style.display = 'none';
    resultHeader.style.display = 'flex';

    resultInfo.textContent = `${total_count} 条结果`;

    if (total_count === 0) {
        resultBody.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center; padding: 40px; font-size: 1.125rem; color: #8a9aaa;font-weight: 400; font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', '思源黑体', sans-serif;">
                    未找到相关内容
                </td>
            </tr>
        `;
        return;
    }

    // 按 order 顺序输出结果
    let html = '';
    order.forEach((key) => {
        const items = data[key] || [];
        items.forEach((item) => {
            html += `
                <tr>
                    <td>${item['汉字']}</td>
                    <td>${item['读音']}</td>
                    <td>${item['释义'] || '暂无'}</td>
                </tr>
            `;
        });
    });

    resultBody.innerHTML = html;
}

function showLoading() {
    emptyState.style.display = 'none';
    resultHeader.style.display = 'none';
    resultBody.innerHTML = `
        <tr>
            <td colspan="3" style="text-align: center; padding: 40px;">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>查询中...</p>
                </div>
            </td>
        </tr>
    `;
}

function showEmptyState(message) {
    resultHeader.style.display = 'none';
    resultBody.innerHTML = '';
    emptyState.style.display = 'block';
    const p = emptyState.querySelector('p');
    if (p) p.textContent = message || '输入内容开始查询';
}

// ============================================
// 切换搜索模式
// ============================================
function setMode(mode) {
    currentMode = mode;

    modeChar.classList.toggle('active', mode === 'char');
    modeMeaning.classList.toggle('active', mode === 'meaning');

    if (mode === 'char') {
        searchInput.placeholder = '输入汉字，支持多个';
    } else {
        searchInput.placeholder = '输入关键词，支持多个';
    }

    lastQuery = '';
    showEmptyState('请输入搜索内容');
}

// ============================================
// 执行搜索
// ============================================
function performSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        showEmptyState('请输入搜索内容');
        return;
    }
    search(query, currentMode);
}

// ============================================
// 事件绑定
// ============================================

// 1. 搜索按钮
searchBtn.addEventListener('click', performSearch);

// 2. 回车键
searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        performSearch();
    }
});

// 3. 输入时显示提示
searchInput.addEventListener('input', function() {
    const query = this.value.trim();
    if (!query) {
        showEmptyState('请输入搜索内容');
        lastQuery = '';
    } else {
        emptyState.style.display = 'none';
        resultHeader.style.display = 'none';
        resultBody.innerHTML = `
            <tr>
                <td colspan="3" style="text-align: center; padding: 40px; font-size: 1.125rem; color: #8a9aaa; font-weight: 400; font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', '思源黑体', sans-serif;">
                    输入完成后点击「查询」按钮
                </td>
            </tr>
        `;
    }
});

// 4. 模式切换
modeChar.addEventListener('click', () => setMode('char'));
modeMeaning.addEventListener('click', () => setMode('meaning'));

// ============================================
// 快捷键
// ============================================
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
    }
});

// ============================================
// 启动
// ============================================
setMode('char');

// URL 参数支持
const urlParams = new URLSearchParams(window.location.search);
const queryParam = urlParams.get('q');
const modeParam = urlParams.get('mode');
if (queryParam) {
    if (modeParam) setMode(modeParam);
    searchInput.value = queryParam;
    lastQuery = '';
    performSearch();
}