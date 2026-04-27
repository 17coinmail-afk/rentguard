from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from bot.database import async_session, User, Payment
from bot.config import PRICE_PER_PROPERTY, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, SUBSCRIPTION_DAYS
from bot.keyboards import subscription_kb, payment_confirm_kb, main_menu_kb
import uuid
import datetime

router = Router()


@router.callback_query(F.data == "subscription")
async def subscription_info(callback: CallbackQuery):
    from bot.config import TRIAL_DAYS
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()
        now = datetime.datetime.utcnow()
        
        if user and user.subscription_end and user.subscription_end > now:
            days_left = (user.subscription_end - now).days
            status = f"💎 Активна ({days_left} дн.)"
            end_date = user.subscription_end.strftime("%d.%m.%Y")
        elif user and user.created_at:
            trial_end = user.created_at + datetime.timedelta(days=TRIAL_DAYS)
            if trial_end > now:
                days_left = (trial_end - now).days
                status = f"🎁 Пробный период ({days_left} дн.)"
                end_date = trial_end.strftime("%d.%m.%Y")
            else:
                status = "❌ Неактивна"
                end_date = "—"
        else:
            status = "🎁 Пробный период (7 дн.)"
            end_date = "—"
    
    text = (
        f"💎 <b>Подписка RentGuard</b>\n\n"
        f"Статус: {status}\n"
        f"До: {end_date}\n\n"
        f"Стоимость: <b>{PRICE_PER_PROPERTY} ₽/мес</b> за объект\n\n"
        "С подпиской доступно:\n"
        "• Неограниченное количество объектов\n"
        "• Автонапоминания об оплате\n"
        "• Контроль просрочек\n"
        "• Фотоучёт\n"
        "• Приоритетная поддержка"
    )
    await callback.message.edit_text(text, reply_markup=subscription_kb())


@router.callback_query(F.data == "buy_sub")
async def buy_subscription(callback: CallbackQuery):
    payment_id = str(uuid.uuid4())
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()
        payment = Payment(
            user_id=user.id,
            amount=PRICE_PER_PROPERTY,
            provider_payment_id=payment_id
        )
        session.add(payment)
        await session.commit()
    
    # Simple payment link generation (mock if no YooKassa creds)
    if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY:
        try:
            from yookassa import Configuration, Payment as YooPayment
            Configuration.account_id = YOOKASSA_SHOP_ID
            Configuration.secret_key = YOOKASSA_SECRET_KEY
            yoo_payment = YooPayment.create({
                "amount": {
                    "value": f"{PRICE_PER_PROPERTY}.00",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/your_bot"
                },
                "capture": True,
                "description": f"Подписка RentGuard на {SUBSCRIPTION_DAYS} дней",
                "metadata": {"user_id": user.id, "payment_id": payment_id}
            })
            url = yoo_payment.confirmation.confirmation_url
            text = f"💎 Перейди по ссылке для оплаты подписки ({PRICE_PER_PROPERTY} ₽):\n\n{url}\n\nПосле оплаты нажми «Я оплатил»"
        except Exception:
            text = f"⚠️ Платёжная система временно недоступна.\nПереведи {PRICE_PER_PROPERTY} ₽ на карту (номер уточни у поддержки) и нажми «Я оплатил»"
    else:
        text = (
            f"💎 Для оплаты подписки ({PRICE_PER_PROPERTY} ₽):\n\n"
            "1. Переведи сумму на карту Т-Банк: <code>0000000000000000</code>\n"
            "2. В комментарии укажи свой Telegram @username\n"
            "3. Нажми «Я оплатил»\n\n"
            "После проверки подписка будет активирована вручную."
        )
    
    await callback.message.edit_text(text, reply_markup=payment_confirm_kb(payment_id))


@router.callback_query(F.data.startswith("check_pay:"))
async def check_payment(callback: CallbackQuery):
    await callback.message.edit_text(
        "⏳ Проверяем оплату...\n"
        "Администратор получил уведомление и скоро активирует подписку.",
        reply_markup=main_menu_kb()
    )
    # Notify admin
    from bot.config import ADMIN_ID
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    bot = callback.bot
    await bot.send_message(
        ADMIN_ID,
        f"💰 Новая оплата от @{callback.from_user.username or callback.from_user.id}\n"
        f"Проверь платёж и активируй подписку через /activate {callback.from_user.id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Активировать", callback_data=f"activate:{callback.from_user.id}")]
        ])
    )


@router.callback_query(F.data.startswith("activate:"))
async def activate_subscription(callback: CallbackQuery):
    from bot.config import ADMIN_ID
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа")
        return
    tg_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user:
            now = datetime.datetime.utcnow()
            if user.subscription_end and user.subscription_end > now:
                user.subscription_end = user.subscription_end + datetime.timedelta(days=SUBSCRIPTION_DAYS)
            else:
                user.subscription_end = now + datetime.timedelta(days=SUBSCRIPTION_DAYS)
            await session.commit()
            await callback.answer("Подписка активирована!")
            await callback.message.edit_text(callback.message.text + "\n\n✅ АКТИВИРОВАНО")
            await callback.bot.send_message(tg_id, "🎉 Ваша подписка активирована! Спасибо за оплату.", reply_markup=main_menu_kb())
