from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from bot.database import async_session, User, Property, Payment
from bot.config import ADMIN_ID
from bot.states import Broadcast
from bot.keyboards import admin_kb, back_to_main_kb

router = Router()


@router.callback_query(F.data == "bot_stats")
async def bot_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа")
        return
    async with async_session() as session:
        users_count = await session.scalar(select(func.count()).select_from(User))
        props_count = await session.scalar(select(func.count()).select_from(Property))
        payments_total = await session.scalar(select(func.sum(Payment.amount)).where(Payment.status == "succeeded"))
    
    text = (
        f"📈 <b>Статистика бота</b>\n\n"
        f"👤 Пользователей: {users_count}\n"
        f"🏠 Объектов: {props_count}\n"
        f"💰 Доход: {payments_total or 0:,.0f} ₽"
    )
    await callback.message.edit_text(text, reply_markup=admin_kb())


@router.callback_query(F.data == "broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа")
        return
    await callback.message.edit_text("Введи текст рассылки для всех пользователей:")
    await state.set_state(Broadcast.message)


@router.message(Broadcast.message)
async def broadcast_confirm(message: Message, state: FSMContext):
    await state.update_data(message=message.text)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        f"Подтверди рассылку:\n\n{message.text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")],
        ])
    )
    await state.set_state(Broadcast.confirm)


@router.callback_query(F.data == "confirm_broadcast", Broadcast.confirm)
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа")
        return
    data = await state.get_data()
    text = data.get("message", "")
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    sent = 0
    failed = 0
    for user in users:
        try:
            await callback.bot.send_message(user.tg_id, text)
            sent += 1
        except Exception:
            failed += 1
    
    await callback.message.edit_text(
        f"📢 Рассылка завершена!\n\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}",
        reply_markup=admin_kb()
    )
    await state.clear()
