const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const CLOUD_KEY = 'rg_properties_v1';

// CloudStorage promise wrappers
function cloudSet(key, value) {
    return new Promise((resolve, reject) => {
        if (!tg.CloudStorage) {
            // Fallback to localStorage for browser testing
            try {
                localStorage.setItem(key, value);
                resolve(true);
            } catch (e) { reject(e); }
            return;
        }
        tg.CloudStorage.setItem(key, value, (err, stored) => {
            if (err) reject(err);
            else resolve(stored);
        });
    });
}

function cloudGet(key) {
    return new Promise((resolve, reject) => {
        if (!tg.CloudStorage) {
            try {
                resolve(localStorage.getItem(key) || null);
            } catch (e) { reject(e); }
            return;
        }
        tg.CloudStorage.getItem(key, (err, value) => {
            if (err) reject(err);
            else resolve(value || null);
        });
    });
}

function cloudRemove(key) {
    return new Promise((resolve, reject) => {
        if (!tg.CloudStorage) {
            try {
                localStorage.removeItem(key);
                resolve(true);
            } catch (e) { reject(e); }
            return;
        }
        tg.CloudStorage.removeItem(key, (err, removed) => {
            if (err) reject(err);
            else resolve(removed);
        });
    });
}

// Data helpers
async function loadData() {
    const raw = await cloudGet(CLOUD_KEY);
    if (!raw) return { properties: [] };
    try {
        return JSON.parse(raw);
    } catch (e) {
        return { properties: [] };
    }
}

async function saveData(data) {
    await cloudSet(CLOUD_KEY, JSON.stringify(data));
}

let appData = { properties: [] };

function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById('page-' + name).classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`button[onclick="showPage('${name}')"]`);
    if (btn) btn.classList.add('active');
    if (name === 'properties') renderProperties();
    if (name === 'stats') renderStats();
}

function loadUser() {
    const user = tg.initDataUnsafe?.user || {};
    const name = user.first_name ? (user.first_name + ' ' + (user.last_name || '')).trim() : 'Пользователь';
    document.getElementById('user-name').textContent = name;
}

function renderProperties() {
    const list = document.getElementById('properties-list');
    const props = appData.properties || [];
    if (props.length === 0) {
        list.innerHTML = '<p>Нет объектов. Добавь первый!</p>';
        return;
    }
    list.innerHTML = props.map((p, idx) => `
        <div class="card">
            <h3>${escapeHtml(p.name)}</h3>
            <p>${escapeHtml(p.address || 'Адрес не указан')}</p>
            <p class="price">${Number(p.rent_amount || 0).toLocaleString()} ₽/мес</p>
            <p>Арендатор: ${escapeHtml(p.tenant_name || '—')}</p>
            <p>Телефон: ${escapeHtml(p.tenant_phone || '—')}</p>
            <p>Оплата: ${p.payment_day || 1} числа</p>
            <button class="delete-btn" onclick="deleteProperty(${idx})">Удалить</button>
        </div>
    `).join('');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function deleteProperty(idx) {
    if (!confirm('Удалить объект?')) return;
    appData.properties.splice(idx, 1);
    await saveData(appData);
    renderProperties();
    tg.HapticFeedback?.impactOccurred('light');
}

function renderStats() {
    const props = appData.properties || [];
    const totalProperties = props.length;
    const totalIncome = props.reduce((sum, p) => sum + (Number(p.rent_amount) || 0), 0);
    document.getElementById('stat-count').textContent = totalProperties;
    document.getElementById('stat-income').textContent = totalIncome.toLocaleString() + ' ₽';
}

document.getElementById('add-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const prop = {
        name: data.name || '',
        address: data.address || '',
        rent_amount: parseFloat(data.rent_amount) || 0,
        payment_day: parseInt(data.payment_day) || 1,
        tenant_name: data.tenant_name || '',
        tenant_phone: data.tenant_phone || '',
        tenant_tg: data.tenant_tg || '',
        deposit: parseFloat(data.deposit) || 0,
    };
    appData.properties.push(prop);
    await saveData(appData);
    tg.showAlert('Объект добавлен!');
    tg.HapticFeedback?.notificationOccurred('success');
    form.reset();
    showPage('properties');
});

async function init() {
    loadUser();
    appData = await loadData();
    renderProperties();
}

init();
