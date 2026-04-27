const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const CLOUD_KEY = 'rg_properties_v1';

function cloudSet(key, value) {
    return new Promise((resolve, reject) => {
        if (!tg.CloudStorage) {
            try { localStorage.setItem(key, value); resolve(true); } catch (e) { reject(e); }
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
            try { resolve(localStorage.getItem(key) || null); } catch (e) { reject(e); }
            return;
        }
        tg.CloudStorage.getItem(key, (err, value) => {
            if (err) reject(err);
            else resolve(value || null);
        });
    });
}

async function loadData() {
    const raw = await cloudGet(CLOUD_KEY);
    if (!raw) return { properties: [] };
    try { return JSON.parse(raw); } catch (e) { return { properties: [] }; }
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
    if (name === 'dashboard') renderDashboard();
    if (name === 'properties') renderProperties();
}

function loadUser() {
    const user = tg.initDataUnsafe?.user || {};
    const name = user.first_name ? (user.first_name + ' ' + (user.last_name || '')).trim() : 'Пользователь';
    document.getElementById('user-name').textContent = name;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderDashboard() {
    const props = appData.properties || [];
    const totalIncome = props.reduce((sum, p) => sum + (Number(p.rent_amount) || 0), 0);
    document.getElementById('dash-count').textContent = props.length;
    document.getElementById('dash-income').textContent = totalIncome.toLocaleString() + ' ₽';

    const today = new Date();
    const currentDay = today.getDate();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();

    const upcoming = props
        .map(p => {
            const day = parseInt(p.payment_day) || 1;
            let paymentDate = new Date(currentYear, currentMonth, day);
            if (day < currentDay) {
                paymentDate = new Date(currentYear, currentMonth + 1, day);
            }
            const daysLeft = Math.ceil((paymentDate - today) / (1000 * 60 * 60 * 24));
            return { ...p, paymentDate, daysLeft };
        })
        .sort((a, b) => a.daysLeft - b.daysLeft)
        .slice(0, 5);

    const list = document.getElementById('payments-list');
    if (upcoming.length === 0) {
        list.innerHTML = '<div class="empty-state">Нет объектов для отображения</div>';
        return;
    }
    list.innerHTML = upcoming.map(p => {
        const dateStr = p.paymentDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
        const daysText = p.daysLeft === 0 ? 'Сегодня!' : p.daysLeft === 1 ? 'Завтра' : `Через ${p.daysLeft} дн.`;
        return `
            <div class="payment-row">
                <div>
                    <div class="payment-name">${escapeHtml(p.name)}</div>
                    <div class="payment-date">${dateStr} · ${daysText}</div>
                </div>
                <div class="payment-amount">${Number(p.rent_amount || 0).toLocaleString()} ₽</div>
            </div>
        `;
    }).join('');
}

function renderProperties() {
    const list = document.getElementById('properties-list');
    const props = appData.properties || [];
    if (props.length === 0) {
        list.innerHTML = '<div class="empty-state">Нет объектов. Добавь первый!</div>';
        return;
    }
    list.innerHTML = props.map((p, idx) => `
        <div class="card">
            <h3>${escapeHtml(p.name)}</h3>
            <p>${escapeHtml(p.address || 'Адрес не указан')}</p>
            <p class="price">${Number(p.rent_amount || 0).toLocaleString()} ₽/мес</p>
            <p>👤 ${escapeHtml(p.tenant_name || '—')} · 📞 ${escapeHtml(p.tenant_phone || '—')}</p>
            <p>📅 Оплата: ${p.payment_day || 1} числа · 💰 Залог: ${Number(p.deposit || 0).toLocaleString()} ₽</p>
            <button class="delete-btn" onclick="deleteProperty(${idx})">Удалить</button>
        </div>
    `).join('');
}

async function deleteProperty(idx) {
    if (!confirm('Удалить объект?')) return;
    appData.properties.splice(idx, 1);
    await saveData(appData);
    renderProperties();
    tg.HapticFeedback?.impactOccurred('light');
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
    showPage('dashboard');
});

async function init() {
    loadUser();
    appData = await loadData();
    renderDashboard();
}

init();
