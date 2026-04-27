from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Мои объекты", callback_data="my_properties")],
        [InlineKeyboardButton(text="➕ Добавить объект", callback_data="add_property")],
        [InlineKeyboardButton(text="💳 Оплата аренды", callback_data="rent_payments")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="statistics")],
        [InlineKeyboardButton(text="📸 Фотоучёт", callback_data="photos")],
        [InlineKeyboardButton(text="💎 Подписка", callback_data="subscription")],
    ])


def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")]
    ])


def property_actions_kb(property_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_prop:{property_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del_prop:{property_id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_properties")],
    ])


def subscription_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку (30 дней)", callback_data="buy_sub")],
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")],
    ])


def payment_confirm_kb(payment_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_pay:{payment_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="subscription")],
    ])


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton(text="📈 Статистика бота", callback_data="bot_stats")],
        [InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")],
    ])