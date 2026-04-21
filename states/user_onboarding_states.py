from aiogram.fsm.state import State, StatesGroup


class UserOnboardingStates(StatesGroup):
    waiting_for_initial_capital = State()