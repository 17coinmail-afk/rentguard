const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const API_BASE = '';

async function api(url, options = {}) {
    const res = await fetch(API_BASE + url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-Telegram-Init-Data': tg.initData,
            ...options.headers
        }
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.getElementById('page-' + name).classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    if (name === 'properties') loadProperties();
    if (name === 'stats') loadStats();
}

async function loadUser() {
    try {
        const user = await api('/api/me');
        document.getElementById('user-name').textContent = user.full_name;
    } catch (e) {
        document.getElementById('user-name').textContent = 'Ошибка авторизации';
    }
}

async function loadProperties() {
    try {
        const props = await api('/api/properties');
        const list = document.getElementById('properties-list');
        if (props.length === 0) {
            list.innerHTML = '<p>Нет объектов. Добавь первый!</p>';
            return;
        }
        list.innerHTML = props.map(p => `
            <div class="card">
                <h3>${p.name}</h3>
                <p>${p.address || 'Адрес не указан'}</p>
                <p class="price">${p.rent_amount.toLocaleString()} ₽/мес</p>
                <p>Арендатор: ${p.tenant_name || '—'}</p>
                <p>Телефон: ${p.tenant_phone || '—'}</p>
                <p>Оплата: ${p.payment_day} числа</p>
                <button class="delete-btn" onclick="deleteProperty(${p.id})">Удалить</button>
            </div>
        `).join('');
    } catch (e) {
        document.getElementById('properties-list').innerHTML = '<p>Ошибка загрузки</p>';
    }
}

async function deleteProperty(id) {
    if (!confirm('Удалить объект?')) return;
    try {
        await api('/api/properties/' + id, { method: 'DELETE' });
        loadProperties();
    } catch (e) {
        alert('Ошибка удаления');
    }
}

async function loadStats() {
    try {
        const stats = await api('/api/stats');
        document.getElementById('stat-count').textContent = stats.total_properties;
        document.getElementById('stat-income').textContent = stats.total_monthly_rent.toLocaleString() + ' ₽';
    } catch (e) {
        console.error(e);
    }
}

document.getElementById('add-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    data.rent_amount = parseFloat(data.rent_amount);
    data.payment_day = parseInt(data.payment_day);
    data.deposit = parseFloat(data.deposit);
    try {
        await api('/api/properties', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        tg.showAlert('Объект добавлен!');
        form.reset();
        showPage('properties');
        loadProperties();
    } catch (err) {
        tg.showAlert('Ошибка: ' + err.message);
    }
});

loadUser();
loadProperties();
