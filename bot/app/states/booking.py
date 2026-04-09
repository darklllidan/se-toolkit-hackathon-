from aiogram.fsm.state import State, StatesGroup


class BookingFSM(StatesGroup):
    choosing_category = State()    # User picks: washing / meeting / rest
    choosing_resource = State()    # User picks a specific machine/room
    choosing_date = State()        # User picks: today / tomorrow / specific date
    choosing_start_time = State()  # User picks an hour slot
    choosing_duration = State()    # User picks 1h / 2h / 3h / 4h
    confirming = State()           # Shows summary, awaits confirm or cancel
