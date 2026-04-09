from fastapi import APIRouter

from app.api.v1 import assistant, auth, bookings, internal_bot, resources, users, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(resources.router)
api_router.include_router(bookings.router)
api_router.include_router(internal_bot.router)
api_router.include_router(ws.router)
api_router.include_router(assistant.router)
