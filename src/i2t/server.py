import base64
import datetime
import mimetypes
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from openai import OpenAI

from config import load_config

config = load_config()
model_cfg = config.model

client = OpenAI(base_url=model_cfg.base_url, api_key=model_cfg.api_key)

DEFAULT_PROMPT = model_cfg.default_prompt
ALLOWED_MIME_TYPES = set(model_cfg.allowed_mime_types)
sampling_args = dict(model_cfg.sampling_args)
extra_args = dict(model_cfg.extra_args)

app = FastAPI(title=config.app.title, version=config.app.version)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _to_data_url(data: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(data).decode()
    return f"data:{mime_type};base64,{encoded}"


def _call_model(image_data: bytes, mime_type: str, prompt: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _to_data_url(image_data, mime_type)}},
            ],
        }
    ]

    start_at = datetime.datetime.now()
    response = client.chat.completions.create(
        model=model_cfg.name,
        messages=messages,
        **sampling_args,
        extra_body=extra_args,
    )
    end_at = datetime.datetime.now()

    return {
        "content": response.choices[0].message.content,
        "usage": response.usage.to_dict(),
        "latency": (end_at - start_at).total_seconds(),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_prompt": DEFAULT_PROMPT,
            "model_name": model_cfg.name,
        },
    )


@app.post("/api/generate")
async def generate(prompt: str = Form(DEFAULT_PROMPT), file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="仅支持 PNG / JPEG / SVG 文件",
        )

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="文件内容为空")

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="无法识别的文件类型")

    try:
        result = _call_model(payload, mime_type, prompt.strip() or DEFAULT_PROMPT)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return JSONResponse(
        {
            "content": result["content"],
            "usage": result["usage"],
            "latency": result["latency"],
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": model_cfg.name}


