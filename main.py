import hashlib
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

EMAIL = "24f2008930@ds.study.iitm.ac.in"   # already trimmed + lowercase

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["*"])

TOOL = {
    "name": "solve_challenge",
    "description": "Returns the exam answer for the current request's challenge header.",
    "inputSchema": {"type": "object", "properties": {}},   # no required props
}

def ok(msg_id, result):
    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": result})

def err(msg_id, code, text):
    return JSONResponse({"jsonrpc": "2.0", "id": msg_id,
                         "error": {"code": code, "message": text}})

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/")
@app.post("/mcp")
async def mcp(request: Request):
    msg = await request.json()
    method = msg.get("method")
    msg_id = msg.get("id")

    # Notifications (like notifications/initialized) have no id: just say "got it"
    if msg_id is None:
        return Response(status_code=202)

    if method == "initialize":
        client_version = (msg.get("params") or {}).get("protocolVersion", "2025-03-26")
        return ok(msg_id, {
            "protocolVersion": client_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "exam-mcp", "version": "1.0.0"},
        })

    if method == "ping":
        return ok(msg_id, {})

    if method == "tools/list":
        return ok(msg_id, {"tools": [TOOL]})

    if method == "tools/call":
        name = (msg.get("params") or {}).get("name")
        if name != "solve_challenge":
            return err(msg_id, -32602, "Unknown tool")
        # The secret note is in the HTTP headers, NOT the JSON body
        challenge = request.headers.get("x-exam-challenge", "").strip()
        if not challenge:
            return ok(msg_id, {"content": [{"type": "text", "text": "missing challenge header"}],
                               "isError": True})
        answer = hashlib.sha256(f"{challenge}:{EMAIL}".encode()).hexdigest()[:16]
        return ok(msg_id, {"content": [{"type": "text", "text": answer}]})

    return err(msg_id, -32601, "Method not found")