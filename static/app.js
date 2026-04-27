const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const CLOUD_KEY = 'rg_properties_v1';
const CLOUD_SUB_KEY = 'rg_subscription_v1';

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

async function loadSub() {
    const raw = await cloudGet(CLOUD_SUB_KEY);
    if (!raw) return { trial_start: new Date().toISOString(), active: true };
    try { return JSON.parse(raw); } catch (e) { return { trial_start: new Date().toISOString(), active: true }; }
}

let appData = { properties: [] };
let subData = { trial_start: new Date().toISOString(), active: true };

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

function getPaymentStatus(prop) {
    const today = new Date();
    const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
    const paymentDay = parseInt(prop.payment_day) || 1;
    const currentDay = today.getDate();
    
    if (prop.last_paid_month === currentMonth) {
        return { status: 'paid', label: '✅ Оплачено', color: '#2ed573' };
    }
    if (currentDay > paymentDay) {
        return { status: 'overdue', label: '⚠️ Просрочено', color: '#ff4757' };
    }
    return { status: 'pending', label: '⏳ Ожидается', color: '#ffa502' };
}

function renderDashboard() {
    const props = appData.properties || [];
    const totalIncome = props.reduce((sum, p) => sum + (Number(p.rent_amount) || 0), 0);
    const paidCount = props.filter(p => getPaymentStatus(p).status === 'paid').length;
    const overdueCount = props.filter(p => getPaymentStatus(p).status === 'overdue').length;
    
    document.getElementById('dash-count').textContent = props.length;
    document.getElementById('dash-income').textContent = totalIncome.toLocaleString() + ' ₽';
    document.getElementById('dash-paid').textContent = paidCount;
    document.getElementById('dash-overdue').textContent = overdueCount;

    // Trial timer
    const trialStart = new Date(subData.trial_start || new Date());
    const trialDays = 7;
    const trialEnd = new Date(trialStart);
    trialEnd.setDate(trialEnd.getDate() + trialDays);
    const daysLeft = Math.ceil((trialEnd - new Date()) / (1000 * 60 * 60 * 24));
    const subEl = document.getElementById('subscription-banner');
    if (daysLeft > 0) {
        subEl.innerHTML = `🎁 Пробный период: <b>${daysLeft} дн.</b> осталось`;
        subEl.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    } else {
        subEl.innerHTML = `💎 Подписка закончилась. <a href="#" onclick="showSubscribe()" style="color:#fff;text-decoration:underline;">Продлить за 500₽/мес</a>`;
        subEl.style.background = '#ff4757';
    }

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
        const st = getPaymentStatus(p);
        const dateStr = p.paymentDate.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
        const daysText = p.daysLeft === 0 ? 'Сегодня!' : p.daysLeft === 1 ? 'Завтра' : `Через ${p.daysLeft} дн.`;
        return `
            <div class="payment-row">
                <div>
                    <div class="payment-name">${escapeHtml(p.name)}</div>
                    <div class="payment-date">${dateStr} · ${daysText}</div>
                </div>
                <div style="text-align:right">
                    <div class="payment-amount">${Number(p.rent_amount || 0).toLocaleString()} ₽</div>
                    <div style="font-size:11px;color:${st.color};font-weight:700">${st.label}</div>
                </div>
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
    list.innerHTML = props.map((p, idx) => {
        const st = getPaymentStatus(p);
        return `
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <h3>${escapeHtml(p.name)}</h3>
                <span style="font-size:12px;color:${st.color};font-weight:700;background:${st.color}15;padding:4px 8px;border-radius:6px">${st.label}</span>
            </div>
            <p>${escapeHtml(p.address || 'Адрес не указан')}</p>
            <p class="price">${Number(p.rent_amount || 0).toLocaleString()} ₽/мес</p>
            <p>👤 ${escapeHtml(p.tenant_name || '—')} · 📞 ${escapeHtml(p.tenant_phone || '—')}</p>
            <p>📅 Оплата: ${p.payment_day || 1} числа · 💰 Залог: ${Number(p.deposit || 0).toLocaleString()} ₽</p>
            <div style="display:flex;gap:8px;margin-top:10px">
                ${st.status !== 'paid' ? `<button class="pay-btn" onclick="markPaid(${idx})">✅ Оплачено</button>` : ''}
                <button class="delete-btn" onclick="deleteProperty(${idx})">Удалить</button>
            </div>
        </div>
    `}).join('');
}

async function markPaid(idx) {
    const today = new Date();
    const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
    appData.properties[idx].last_paid_month = currentMonth;
    await saveData(appData);
    renderProperties();
    tg.HapticFeedback?.notificationOccurred('success');
    tg.showAlert('Отмечено как оплачено!');
}

async function deleteProperty(idx) {
    if (!confirm('Удалить объект?')) return;
    appData.properties.splice(idx, 1);
    await saveData(appData);
    renderProperties();
    tg.HapticFeedback?.impactOccurred('light');
}

function showSubscribe() {
    tg.showAlert(
        '💎 Подписка RentGuard\n\n' +
        '500₽ / месяц за объект\n' +
        'Первые 7 дней бесплатно\n\n' +
        'Для оплаты напишите @airroyalty_bot'
    );
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
        last_paid_month: null,
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
    subData = await loadSub();
    renderDashboard();
}

init();
