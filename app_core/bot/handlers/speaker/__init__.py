from .presentation import router as presentation_router
from .questions import router as questions_router
from .applications import router as applications_router
from .mode_switch import router as mode_switch_router

speaker_router = presentation_router
speaker_router.include_router(questions_router)
speaker_router.include_router(applications_router)
speaker_router.include_router(mode_switch_router)

__all__ = ['speaker_router']