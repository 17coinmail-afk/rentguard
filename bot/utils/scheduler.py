from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from bot.database import async_session, User, Property, RentPayment
from bot.config import ADMIN_ID
import datetime

scheduler = AsyncIOScheduler()


async def check_rent_payments(bot):
    """Check for upcoming and overdue payments and notify landlords"""
    now = datetime.datetime.utcnow()
    async with async_session() as session:
        # Find payments due in 3 days or overdue
        result = await session.execute(
            select(RentPayment).where(
                RentPayment.status.in_(["pending", "overdue"]),
                RentPayment.due_date <= now + datetime.timedelta(days=3)
            )
        )
        payments = result.scalars().all()
        
        for payment in payments:
            prop = payment.property
            if not prop or not prop.owner:
                continue
            
            user = prop.owner
            days_left = (payment.due_date - now).days
            
            if days_left < 0 and payment.status != "overdue":
                payment.status = "overdue"
                await session.commit()
                text = (
                    f"⚠️ <b>Просрочен платёж!</b>\n\n"
                    f"🏠 {prop.name}\n"
                    f"💰 Сумма: {payment.amount:,.0f} ₽\n"
                    f"👤 Арендатор: {prop.tenant_name}\n"
                    f"📞 {prop.tenant_phone or '—'}"
                )
                try:
                    await bot.send_message(user.tg_id, text)
                except Exception:
                    pass
            elif days_left in [3, 1, 0] and payment.status == "pending":
                text = (
                    f"⏰ <b>Напоминание об оплате</b>\n\n"
                    f"🏠 {prop.name}\n"
                    f"💰 Сумма: {payment.amount:,.0f} ₽\n"
                    f"📅 Дата оплаты: {payment.due_date.strftime('%d.%m.%Y')}\n"
                    f"👤 Арендатор: {prop.tenant_name}\n"
                    f"📞 {prop.tenant_phone or '—'}"
                )
                try:
                    await bot.send_message(user.tg_id, text)
                except Exception:
                    pass


async def create_monthly_payments():
    """Create new rent payments for next month when current is paid"""
    now = datetime.datetime.utcnow()
    async with async_session() as session:
        result = await session.execute(
            select(RentPayment).where(
                RentPayment.status == "paid",
                RentPayment.payment_type == "rent",
                RentPayment.paid_date <= now
            )
        )
        payments = result.scalars().all()
        
        for payment in payments:
            prop = payment.property
            if not prop:
                continue
            
            # Check if next month payment already exists
            next_due = payment.due_date
            if next_due.month == 12:
                next_due = next_due.replace(year=next_due.year + 1, month=1)
            else:
                next_due = next_due.replace(month=next_due.month + 1)
            
            existing = await session.execute(
                select(RentPayment).where(
                    RentPayment.property_id == prop.id,
                    RentPayment.due_date == next_due
                )
            )
            if not existing.scalar_one_or_none():
                new_payment = RentPayment(
                    property_id=prop.id,
                    amount=payment.amount,
                    payment_type="rent",
                    due_date=next_due
                )
                session.add(new_payment)
        
        await session.commit()


def setup_scheduler(bot):
    scheduler.add_job(check_rent_payments, "cron", hour=9, minute=0, args=[bot])
    scheduler.add_job(create_monthly_payments, "cron", hour=0, minute=5)
    scheduler.start()