"""Notification orchestrator websocket gateway."""

from __future__ import annotations

from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

connections: Dict[str, set[WebSocket]] = {}


async def register(tenant_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    connections.setdefault(tenant_id, set()).add(websocket)


async def unregister(tenant_id: str, websocket: WebSocket) -> None:
    connections.get(tenant_id, set()).discard(websocket)


@router.websocket("/ws/notifications/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str) -> None:
    await register(tenant_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # keepalive, ignore
    except WebSocketDisconnect:
        await unregister(tenant_id, websocket)
