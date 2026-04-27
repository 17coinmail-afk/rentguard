import logging
from datetime import datetime, timedelta, date
from sqlalchemy import select, and_
from bot.database import async_session, Property, User, ReminderLog

logger = logging.getLogger(__name__)


def build_owner_message(prop, reminder_type):
    name = prop.name
    tenant = prop.tenant_name or "Арендатор"
    amount = f"{prop.rent_amount:,.0f}" if prop.rent_amount else "0"
    day = prop.payment_day or 1

    if reminder_type == "before_1day":
        return (
            f"📅 <b>Напоминание</b>\n\n"
            f"Завтра ({day}-е число) <b>{tenant}</b> должен заплатить "
            f"<b>{amount} ₽</b> за «{name}»."
        )
    elif reminder_type == "on_day":
        return (
            f"💰 <b>День оплаты</b>\n\n"
            f"Сегодня ({day}-е число) ожидается оплата от <b>{tenant}</b> — "
            f"<b>{amount} ₽</b> за «{name}»."
        )
    elif reminder_type == "overdue":
        return (
            f"⚠️ <b>Просрочка!</b>\n\n"
            f"<b>{tenant}</b> не заплатил <b>{amount} ₽</b> за «{name}» "
            f"(должен был {day}-го числа)."
        )
    return ""


async def send_reminder(bot, session, prop, user, reminder_type, year, month):
    """Send reminder if not already sent this month."""
    result = await session.execute(
        select(ReminderLog).where(
            and_(
                ReminderLog.property_id == prop.id,
                ReminderLog.reminder_type == reminder_type,
                ReminderLog.year == year,
                ReminderLog.month == month,
            )
        )
    )
    if result.scalar_one_or_none():
        return  # Already sent

    msg = build_owner_message(prop, reminder_type)
    try:
        await bot.send_message(user.tg_id, msg, parse_mode="HTML")
        log = ReminderLog(
            property_id=prop.id,
            year=year,
            month=month,
            reminder_type=reminder_type,
        )
        session.add(log)
        await session.commit()
        logger.info(f"Sent {reminder_type} reminder for property {prop.id}")
    except Exception as e:
        logger.error(f"Failed to send reminder to {user.tg_id}: {e}")


async def check_and_send_reminders(bot):
    """Check all properties and send due reminders."""
    today = date.today()
    year, month = today.year, today.month

    async with async_session() as session:
        result = await session.execute(select(Property))
        properties = result.scalars().all()

        for prop in properties:
            payment_day = prop.payment_day or 1

            # Calculate payment date for current month
            try:
                payment_date = date(year, month, payment_day)
            except ValueError:
                # e.g. Feb 30
                continue

            # Get owner
            user_result = await session.execute(
                select(User).where(User.id == prop.owner_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                continue

            # Reminder 1 day before
            if today == payment_date - timedelta(days=1):
                await send_reminder(bot, session, prop, user, "before_1day", year, month)

            # Reminder on payment day
            elif today == payment_date:
                await send_reminder(bot, session, prop, user, "on_day", year, month)

            # Overdue notice 1 day after
            elif today == payment_date + timedelta(days=1):
                await send_reminder(bot, session, prop, user, "overdue", year, month)
