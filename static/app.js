const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const CLOUD_KEY = 'rg_properties_v2';
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
    document.querySelectorAll('.bottom-nav-item').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.bottom-nav-item[data-page="${name}"]`);
    if (btn) btn.classList.add('active');
    if (name === 'dashboard') renderDashboard();
    if (name === 'properties') renderProperties();
    if (name === 'profile') renderProfile();
}

function loadUser() {
    const user = tg.initDataUnsafe?.user || {};
    const name = user.first_name ? (user.first_name + ' ' + (user.last_name || '')).trim() : 'Пользователь';
    document.getElementById('user-name').textContent = 'Добро пожаловать, ' + name;
    document.getElementById('profile-name').textContent = name;
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
        return { status: 'paid', label: 'Оплачено', class: 'status-paid' };
    }
    if (currentDay > paymentDay) {
        return { status: 'overdue', label: 'Просрочено', class: 'status-overdue' };
    }
    return { status: 'pending', label: 'Ожидается', class: 'status-pending' };
}

function getDaysUntil(dateStr) {
    if (!dateStr) return null;
    const end = new Date(dateStr);
    const today = new Date();
    const diff = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
    return diff;
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

    // Trial chip
    const trialStart = new Date(subData.trial_start || new Date());
    const trialDays = 7;
    const trialEnd = new Date(trialStart);
    trialEnd.setDate(trialEnd.getDate() + trialDays);
    const daysLeft = Math.ceil((trialEnd - new Date()) / (1000 * 60 * 60 * 24));
    const chip = document.getElementById('subscription-chip');
    if (daysLeft > 0) {
        chip.textContent = '🎁 ' + daysLeft + ' дн. бесплатно';
        chip.style.background = 'rgba(255,255,255,0.2)';
    } else {
        chip.textContent = '💎 Продлить подписку';
        chip.style.background = 'rgba(255,71,87,0.3)';
        chip.style.cursor = 'pointer';
        chip.onclick = showSubscribe;
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
                    <span class="payment-status ${st.class}">${st.label}</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderProperties() {
    const list = document.getElementById('properties-list');
    const props = appData.properties || [];
    if (props.length === 0) {
        list.innerHTML = '<div class="empty-state">Нет объектов.<br>Нажми + чтобы добавить первый!</div>';
        return;
    }
    list.innerHTML = props.map((p, idx) => {
        const st = getPaymentStatus(p);
        const leaseDays = getDaysUntil(p.lease_end);
        let leaseText = '';
        if (leaseDays !== null) {
            if (leaseDays < 0) leaseText = `🔴 Договор просрочен (${Math.abs(leaseDays)} дн.)`;
            else if (leaseDays <= 30) leaseText = `🟡 Договор заканчивается через ${leaseDays} дн.`;
            else leaseText = `🟢 Договор до ${new Date(p.lease_end).toLocaleDateString('ru-RU')}`;
        }
        return `
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
                <h3>${escapeHtml(p.name)}</h3>
                <span class="status-badge-inline ${st.class}">${st.label}</span>
            </div>
            <p>📍 ${escapeHtml(p.address || 'Адрес не указан')}</p>
            <p class="price">${Number(p.rent_amount || 0).toLocaleString()} ₽/мес</p>
            <p>👤 ${escapeHtml(p.tenant_name || '—')} · 📞 ${escapeHtml(p.tenant_phone || '—')}</p>
            <p>📅 Оплата: ${p.payment_day || 1} числа · 💰 Залог: ${Number(p.deposit || 0).toLocaleString()} ₽</p>
            ${leaseText ? `<p style="font-size:12px;margin-top:4px">${leaseText}</p>` : ''}
            <div class="btn-row">
                ${st.status !== 'paid' ? `<button class="btn-small btn-pay" onclick="markPaid(${idx})">✅ Оплачено</button>` : ''}
                <button class="btn-small btn-requisites" onclick="sendRequisites(${idx})">💳 Реквизиты</button>
                <button class="btn-small btn-contract" onclick="generateContract(${idx})">📄 Договор</button>
                <button class="btn-small btn-delete" onclick="deleteProperty(${idx})">🗑 Удалить</button>
            </div>
        </div>
    `}).join('');
}

function renderProfile() {
    const trialStart = new Date(subData.trial_start || new Date());
    const trialEnd = new Date(trialStart);
    trialEnd.setDate(trialEnd.getDate() + 7);
    const daysLeft = Math.ceil((trialEnd - new Date()) / (1000 * 60 * 60 * 24));
    const statusEl = document.getElementById('profile-status');
    if (daysLeft > 0) {
        statusEl.textContent = `🎁 Пробный период: ${daysLeft} дн.`;
        statusEl.style.background = 'rgba(46,213,115,0.3)';
    } else {
        statusEl.textContent = '💎 Подписка неактивна';
        statusEl.style.background = 'rgba(255,71,87,0.3)';
    }
}

async function markPaid(idx) {
    const today = new Date();
    const currentMonth = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0');
    appData.properties[idx].last_paid_month = currentMonth;
    await saveData(appData);
    renderProperties();
    tg.HapticFeedback?.notificationOccurred('success');
    tg.showAlert('✅ Отмечено как оплачено');
}

function sendRequisites(idx) {
    const p = appData.properties[idx];
    const text = `💳 Реквизиты для оплаты аренды\n\nОбъект: ${p.name}\nАдрес: ${p.address || '—'}\nСумма: ${Number(p.rent_amount || 0).toLocaleString()} ₽/мес\nДень оплаты: ${p.payment_day || 1} числа\n\nПожалуйста, переведите сумму вовремя. Спасибо!`;
    tg.showAlert(text);
}

async function generateContract(idx) {
    const p = appData.properties[idx];
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    doc.setFontSize(18);
    doc.text('ДОГОВОР АРЕНДЫ ЖИЛОГО ПОМЕЩЕНИЯ', 105, 20, { align: 'center' });
    
    doc.setFontSize(12);
    const text = `
1. ПРЕДМЕТ ДОГОВОРА
Арендодатель предоставляет, а Арендатор принимает во временное пользование квартиру:
${p.address || '_________________________________'}

2. СРОК ДЕЙСТВИЯ
Договор заключен с "___"________ 20__ г. по "___"________ 20__ г.
${p.lease_end ? '(Предполагаемый срок: ' + new Date(p.lease_end).toLocaleDateString('ru-RU') + ')' : ''}

3. АРЕНДНАЯ ПЛАТА
Ежемесячная арендная плата составляет: ${Number(p.rent_amount || 0).toLocaleString()} ₽
Оплата производится: ${p.payment_day || 1} числа каждого месяца
Залог: ${Number(p.deposit || 0).toLocaleString()} ₽

4. СТОРОНЫ
Арендатор: ${p.tenant_name || '_________________________________'}
Телефон: ${p.tenant_phone || '_________________________________'}

5. ПОДПИСИ СТОРОН
_______________________ / _______________________        _________________________ / _______________________
      (Арендодатель)                                               (Арендатор)

Дата составления: ${new Date().toLocaleDateString('ru-RU')}
    `;
    
    const lines = doc.splitTextToSize(text, 180);
    doc.text(lines, 15, 35);
    
    const filename = `dogovor_${(p.name || 'object').replace(/\s+/g, '_')}.pdf`;
    doc.save(filename);
    tg.HapticFeedback?.notificationOccurred('success');
}

async function deleteProperty(idx) {
    if (!confirm('Удалить объект «' + (appData.properties[idx].name || '') + '»?')) return;
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
        lease_end: data.lease_end || null,
        tenant_name: data.tenant_name || '',
        tenant_phone: data.tenant_phone || '',
        tenant_tg: data.tenant_tg || '',
        deposit: parseFloat(data.deposit) || 0,
        last_paid_month: null,
    };
    appData.properties.push(prop);
    await saveData(appData);
    tg.showAlert('🏠 Объект добавлен!');
    tg.HapticFeedback?.notificationOccurred('success');
    form.reset();
    showPage('properties');
});

async function init() {
    loadUser();
    appData = await loadData();
    subData = await loadSub();
    renderDashboard();
}

init();
