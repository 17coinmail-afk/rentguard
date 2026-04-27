async def notify_admin_new_user(bot, admin_id, user):
    text = (
        f"👤 <b>Новый пользователь</b>\n\n"
        f"Имя: {user.full_name}\n"
        f"Username: @{user.username or '—'}\n"
        f"ID: {user.tg_id}"
    )
    try:
        await bot.send_message(admin_id, text)
    except Exception:
        pass


async def notify_payment_received(bot, admin_id, user, amount):
    text = (
        f"💰 <b>Новая оплата</b>\n\n"
        f"Пользователь: {user.full_name} (@{user.username or '—'})\n"
        f"Сумма: {amount:,.0f} ₽"
    )
    try:
        await bot.send_message(admin_id, text)
    except Exception:
        pass