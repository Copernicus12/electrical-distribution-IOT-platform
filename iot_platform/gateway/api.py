"""HTTP and WebSocket ingestion endpoints sharing the edge Gateway instance."""

import json
import os


def create_app(gateway):
    try:
        from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
    except ImportError as exc:
        raise RuntimeError("Install the project dependencies with: pip install -r requirements.txt") from exc

    app = FastAPI(title="Electrical Distribution Edge Gateway")
    access_token = os.environ.get("IOT_HTTPS_TOKEN")

    @app.get("/health")
    async def health():
        return {"ok": True, "received_messages": gateway.count}

    @app.post("/telemetry")
    async def telemetry(message: dict, authorization: str = Header(default="")):
        if access_token and authorization != "Bearer " + access_token:
            raise HTTPException(status_code=401, detail="invalid bearer token")
        try:
            body = json.dumps(message, allow_nan=False).encode("utf-8")
            if len(body) > 64 * 1024:
                raise HTTPException(status_code=413, detail="telemetry message is too large")
            return gateway.accept(body)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.websocket("/ws")
    async def websocket_telemetry(websocket: WebSocket):
        if access_token and websocket.headers.get("authorization") != "Bearer " + access_token:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            while True:
                body = await websocket.receive_text()
                try:
                    response = gateway.accept(body.encode("utf-8"))
                except (ValueError, TypeError) as exc:
                    await websocket.send_text(json.dumps({"accepted": False, "error": str(exc)}))
                    continue
                await websocket.send_text(json.dumps(response, allow_nan=False))
        except WebSocketDisconnect:
            return

    return app
