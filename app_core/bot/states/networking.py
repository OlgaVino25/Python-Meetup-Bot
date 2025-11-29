from aiogram.fsm.state import State, StatesGroup

class NetworkingStates(StatesGroup):
    waiting_name = State()
    waiting_username = State()
    waiting_company = State()
    waiting_job_title = State()
    waiting_interests = State()
    waiting_contact_consent = State()
    browsing_profiles = State()