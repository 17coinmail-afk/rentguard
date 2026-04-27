from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from bot.database import async_session, User, Property, RentPayment
from bot.states import AddProperty
from bot.keyboards import main_menu_kb, back_to_main_kb, property_actions_kb
import datetime

router = Router()


def check_subscription(func):
    async def wrapper(*args, **kwargs):
        obj = args[0]
        tg_id = obj.from_user.id if isinstance(obj, Message) else obj.from_user.id
        async with async_session() as session:
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalar_one_or_none()
            if not user or not user.subscription_end or user.subscription_end < datetime.datetime.utcnow():
                msg = obj if isinstance(obj, Message) else obj.message
                await msg.answer(
                    "⛔ Действие доступно только по подписке.\n"
                    f"💎 Оформи подписку в главном меню.",
                    reply_markup=main_menu_kb()
                )
                return
        return await func(*args, **kwargs)
    return wrapper


@router.callback_query(F.data == "my_properties")
async def my_properties(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
        user = result.scalar_one_or_none()
        if not user or not user.properties:
            await callback.message.edit_text(
                "🏠 У тебя пока нет объектов.\nНажми «Добавить объект» в меню.",
                reply_markup=back_to_main_kb()
            )
            return
        
        text = "🏠 <b>Твои объекты:</b>\n\n"
        kb = []
        for prop in user.properties:
            text += f"• <b>{prop.name}</b> — {prop.address or 'адрес не указан'}\n"
            kb.append([InlineKeyboardButton(text=prop.name, callback_data=f"prop:{prop.id}")])
        kb.append([InlineKeyboardButton(text="◀️ В главное меню", callback_data="main_menu")])
        from aiogram.types import InlineKeyboardMarkup
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data == "add_property")
async def add_property_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введи название объекта (например, «2-к квартира на Ленина»):")
    await state.set_state(AddProperty.name)


@router.message(AddProperty.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введи адрес объекта:")
    await state.set_state(AddProperty.address)


@router.message(AddProperty.address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Введи сумму аренды в месяц (руб):")
    await state.set_state(AddProperty.rent_amount)


@router.message(AddProperty.rent_amount)
async def process_rent(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(" ", "").replace(",", "."))
        await state.update_data(rent_amount=amount)
        await message.answer("Введи день месяца для оплаты аренды (1-31):")
        await state.set_state(AddProperty.payment_day)
    except ValueError:
        await message.answer("❌ Введи число. Попробуй ещё раз:")


@router.message(AddProperty.payment_day)
async def process_day(message: Message, state: FSMContext):
    try:
        day = int(message.text)
        if not 1 <= day <= 31:
            raise ValueError
        await state.update_data(payment_day=day)
        await message.answer("Введи ФИО арендатора:")
        await state.set_state(AddProperty.tenant_name)
    except ValueError:
        await message.answer("❌ Введи число от 1 до 31:")


@router.message(AddProperty.tenant_name)
async def process_tenant_name(message: Message, state: FSMContext):
    await state.update_data(tenant_name=message.text)
    await message.answer("Введи телефон арендатора (или отправь '-'):")
    await state.set_state(AddProperty.tenant_phone)


@router.message(AddProperty.tenant_phone)
async def process_tenant_phone(message: Message, state: FSMContext):
    await state.update_data(tenant_phone=message.text)
    await message.answer("Введи Telegram арендатора (@username или '-'):")
    await state.set_state(AddProperty.tenant_tg)


@router.message(AddProperty.tenant_tg)
async def process_tenant_tg(message: Message, state: FSMContext):
    await state.update_data(tenant_tg=message.text)
    await message.answer("Введи сумму залога (руб, 0 если нет):")
    await state.set_state(AddProperty.deposit)


@router.message(AddProperty.deposit)
async def process_deposit(message: Message, state: FSMContext):
    try:
        deposit = float(message.text.replace(" ", "").replace(",", "."))
        data = await state.get_data()
        
        async with async_session() as session:
            result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
            user = result.scalar_one_or_none()
            
            prop = Property(
                owner_id=user.id,
                name=data["name"],
                address=data["address"],
                rent_amount=data["rent_amount"],
                payment_day=int(data["payment_day"]),
                tenant_name=data["tenant_name"],
                tenant_phone=data["tenant_phone"],
                tenant_tg=data["tenant_tg"],
                deposit=deposit
            )
            session.add(prop)
            await session.flush()
            
            # Create first rent payment
            today = datetime.datetime.utcnow()
            due = today.replace(day=int(data["payment_day"]))
            if due < today:
                if today.month == 12:
                    due = due.replace(year=today.year+1, month=1)
                else:
                    due = due.replace(month=today.month+1)
            
            payment = RentPayment(
                property_id=prop.id,
                amount=data["rent_amount"],
                payment_type="rent",
                due_date=due
            )
            session.add(payment)
            await session.commit()
        
        await message.answer(
            f"✅ Объект <b>{data['name']}</b> добавлен!\n\n"
            f"Следующая оплата: {due.strftime('%d.%m.%Y')}",
            reply_markup=main_menu_kb()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введи число:")


@router.callback_query(F.data.startswith("prop:"))
async def property_detail(callback: CallbackQuery):
    prop_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(select(Property).where(Property.id == prop_id))
        prop = result.scalar_one_or_none()
        if not prop:
            await callback.answer("Объект не найден")
            return
        
        text = (
            f"🏠 <b>{prop.name}</b>\n"
            f"📍 {prop.address or '—'}\n"
            f"💰 Аренда: {prop.rent_amount:,.0f} ₽/мес\n"
            f"📅 Оплата: {prop.payment_day} числа\n"
            f"👤 Арендатор: {prop.tenant_name}\n"
            f"📞 {prop.tenant_phone or '—'}\n"
            f"💬 {prop.tenant_tg or '—'}\n"
            f"🔐 Залог: {prop.deposit:,.0f} ₽"
        )
        await callback.message.edit_text(text, reply_markup=property_actions_kb(prop.id))