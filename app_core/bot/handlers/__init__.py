from .start import router as start_router
from .program import router as program_router
from .questions import router as questions_router
from .networking import router as networking_router
from .donations import router as donations_router
from .help import router as help_router
from .admin import router as admin_router
from .subscription import router as subscription_router
from .speaker import speaker_router

__all__ = [
    'start_router',
    'program_router', 
    'questions_router',
    'networking_router',
    'donations_router',
    'help_router',
    'admin_router',
    'subscription_router',
    'speaker_router'
]