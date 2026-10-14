from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_car = State()
    waiting_for_trouble = State()

class AIDiagnosticStates(StatesGroup):
    waiting_for_symptoms = State()
