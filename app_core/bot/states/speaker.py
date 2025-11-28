from aiogram.fsm.state import State, StatesGroup

class SpeakerStates(StatesGroup):
    presentation_active = State()

class SpeakerApplicationStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_description = State() 
    waiting_for_duration = State()
    confirmation = State()