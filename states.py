from aiogram.fsm.state import StatesGroup, State

class LinkProcess(StatesGroup):
    waiting_for_link = State()