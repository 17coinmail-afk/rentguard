from aiogram.fsm.state import State, StatesGroup


class AddProperty(StatesGroup):
    name = State()
    address = State()
    rent_amount = State()
    payment_day = State()
    tenant_name = State()
    tenant_phone = State()
    tenant_tg = State()
    deposit = State()


class AddPayment(StatesGroup):
    property_id = State()
    amount = State()
    payment_type = State()
    due_date = State()
    comment = State()


class AddPhoto(StatesGroup):
    property_id = State()
    photo_type = State()
    description = State()
    photo = State()


class Broadcast(StatesGroup):
    message = State()
    confirm = State()