from fastapi import APIRouter
from app.api.v1.endpoints import auth, public, events, volunteers, event_token

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(volunteers.router, prefix="/volunteers", tags=["volunteers"])
api_router.include_router(event_token.router, tags=["event-token"])
