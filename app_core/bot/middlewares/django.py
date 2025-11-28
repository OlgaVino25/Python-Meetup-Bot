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
        print(f"DEBUG MIDDLEWARE: Start processing event type: {type(event).__name__}")
        
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)
        
        from_user = event.from_user
        if not from_user:
            return await handler(event, data)
        
        print(f"DEBUG MIDDLEWARE: Processing user ID: {from_user.id}")
        
        from app_core.models import User
        from django.core.exceptions import ObjectDoesNotExist
        
        try:
            user = await sync_to_async(User.objects.get)(
                telegram_id=str(from_user.id)
            )
            print(f"DEBUG MIDDLEWARE: User found: {user.first_name} (ID: {user.telegram_id})")
        except ObjectDoesNotExist:
            user = await sync_to_async(User.objects.create)(
                telegram_id=str(from_user.id),
                username=from_user.username or "",
                first_name=from_user.first_name or "",
                last_name=from_user.last_name or "",
                role="guest"
            )
            print(f"DEBUG MIDDLEWARE: User created: {user.first_name} (ID: {user.telegram_id})")
        
        data['user'] = user
        print(f"DEBUG MIDDLEWARE: User added to data, keys in data: {list(data.keys())}")
        
        result = await handler(event, data)
        print(f"DEBUG MIDDLEWARE: Handler completed successfully")
        return result