"""WebSocket broadcast per event: when volunteers update data, admin control room refreshes."""
import asyncio
import logging
from typing import Dict, Optional, Set

from fastapi import WebSocket

log = logging.getLogger(__name__)

# event_id -> set of WebSocket connections (admin control room viewers)
_connections: Dict[int, Set[WebSocket]] = {}
_lock = asyncio.Lock()
# Set at app startup (lifespan) so sync endpoints can schedule broadcast
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


async def subscribe(event_id: int, websocket: WebSocket) -> None:
    async with _lock:
        if event_id not in _connections:
            _connections[event_id] = set()
        _connections[event_id].add(websocket)
    log.debug("WS subscribe event_id=%s connections=%s", event_id, len(_connections.get(event_id, [])))


async def unsubscribe(event_id: int, websocket: WebSocket) -> None:
    async with _lock:
        if event_id in _connections:
            _connections[event_id].discard(websocket)
            if not _connections[event_id]:
                del _connections[event_id]


def broadcast_event_updated_sync(event_id: int) -> None:
    """Call from sync code (e.g. after DB commit) to notify admin clients. Schedules async broadcast."""
    if _main_loop is None:
        return
    try:
        asyncio.run_coroutine_threadsafe(_broadcast(event_id), _main_loop)
    except Exception as e:
        log.debug("broadcast_event_updated_sync: %s", e)


async def _broadcast(event_id: int) -> None:
    async with _lock:
        conns = set(_connections.get(event_id, []))
    if not conns:
        return
    dead = set()
    for ws in conns:
        try:
            await ws.send_json({"type": "event_updated"})
        except Exception as e:
            log.debug("WS send failed: %s", e)
            dead.add(ws)
    if dead:
        async with _lock:
            if event_id in _connections:
                _connections[event_id] -= dead
                if not _connections[event_id]:
                    del _connections[event_id]
