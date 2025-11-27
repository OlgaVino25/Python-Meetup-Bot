from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

class DjangoORMMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
        
        from_user = event.from_user
        if not from_user:
            return await handler(event, data)
        
        from app_core.models import User
        from django.core.exceptions import ObjectDoesNotExist
        
        try:
            user = await sync_to_async(User.objects.get)(
                telegram_id=str(from_user.id)
            )
        except ObjectDoesNotExist:
            user = await sync_to_async(User.objects.create)(
                telegram_id=str(from_user.id),
                username=from_user.username or "",
                first_name=from_user.first_name or "",
                last_name=from_user.last_name or "",
                role="guest"
            )
        
        data['user'] = user
        return await handler(event, data)