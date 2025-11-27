from . import presentation, questions, applications, mode_switch

from aiogram import Router

speaker_router = Router()
speaker_router.include_router(presentation.router)
speaker_router.include_router(questions.router)
speaker_router.include_router(applications.router)
speaker_router.include_router(mode_switch.router)