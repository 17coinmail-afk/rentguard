# 🚀 Быстрый деплой RentGuard

## Вариант 1: Render.com (бесплатно, проще всего)

1. Зарегистрируйся на [render.com](https://render.com) через GitHub
2. Создай новый **Private** репозиторий на GitHub, залей туда проект
3. В Render нажми **New → Web Service → Connect your GitHub repo**
4. Выбери репозиторий, Render сам найдёт `render.yaml`
5. В настройках сервиса добавь **Environment Variables**:
   - `BOT_TOKEN` = `8634685817:AAFTpSYoYR7w_B9WLgWzGOh-K_FsK09-w38`
   - `ADMIN_ID` = твой числовой ID из @userinfobot
6. Нажми **Deploy**
7. Готово! Бот работает 24/7

> ⚠️ На бесплатном тарифе Render "засыпает" при 15 минутах неактивности, но по входящему сообщению в бота он просыпается мгновенно.

## Вариант 2: Railway.app (бесплатно)

1. Зарегистрируйся на [railway.app](https://railway.app)
2. Создай проект из GitHub-репозитория
3. Добавь Variables в Settings
4. Deploy

## Вариант 3: VPS / Облако (Yandex Cloud, Timeweb, Beget)

Если хочешь стабильность — арендуй VPS за 200-400 ₽/мес:

```bash
# На сервере:
git clone <твой-репозиторий>
cd RentGuard
cp .env.example .env
# отредактируй .env
sudo docker-compose up --build -d
```

## Где взять ADMIN_ID?

1. Напиши [@userinfobot](https://t.me/userinfobot)
2. Он пришлёт твой ID (например, `123456789`)
3. Впиши это число в `.env` или в переменные окружения на сервере

## После деплоя

- Открой бота в Telegram, нажми `/start`
- Если ты админ — отправь `/admin` для панели управления
- Лендинг залей отдельно на GitHub Pages или Netlify (папка `landing/`)

---

**Важно:** я не могу сам зайти на твои аккаунты и задеплоить — у меня нет доступа. Но всё подготовлено: тебе нужно только нажать 3 кнопки на Render. Это займёт 5 минут.

Когда задеплоишь — бот будет работать автономно. Пиши, если нужна помощь!