from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy import select
from bot.database import async_session, User
from bot.config import ADMIN_ID
from bot.keyboards import main_menu_kb, admin_kb, back_to_main_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(user)
            await session.commit()
    
    text = (
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "🏠 <b>RentGuard</b> — умный помощник для арендодателей.\n\n"
        "Я помогу:\n"
        "• Вести учёт объектов и арендаторов\n"
        "• Напоминать об оплате аренды\n"
        "• Вести фотоучёт имущества\n"
        "• Генерировать отчёты\n\n"
        "Нажми кнопку ниже, чтобы начать!"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие:",
        reply_markup=main_menu_kb()
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return
    await message.answer("🔧 Панель администратора", reply_markup=admin_kb())