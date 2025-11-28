import base64
import datetime
import logging
import mimetypes
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from openai import OpenAI

from config import load_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

config = load_config()
model_cfg = config.model
openrouter_cfg = config.openrouter

# 本地模型客户端
local_client = OpenAI(base_url=model_cfg.base_url, api_key=model_cfg.api_key)

# OpenRouter 客户端（如果启用）
openrouter_client = None
if openrouter_cfg.enabled and openrouter_cfg.api_key:
    logger.info(f"初始化 OpenRouter 客户端: base_url={openrouter_cfg.base_url}")
    # OpenRouter 需要特定的请求头
    openrouter_client = OpenAI(
        base_url=openrouter_cfg.base_url,
        api_key=openrouter_cfg.api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",  # 可选：你的应用URL
            "X-Title": "VLM Test",  # 可选：你的应用名称
        },
    )
    logger.info(f"OpenRouter 可用模型数量: {len(openrouter_cfg.models)}")
    for model in openrouter_cfg.models:
        logger.info(f"  - {model.name} ({model.display_name})")
else:
    logger.warning("OpenRouter 未启用或未配置 API Key")

DEFAULT_PROMPT = model_cfg.default_prompt
ALLOWED_MIME_TYPES = set(model_cfg.allowed_mime_types)
local_sampling_args = dict(model_cfg.sampling_args)
local_extra_args = dict(model_cfg.extra_args)

app = FastAPI(title=config.app.title, version=config.app.version)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _to_data_url(data: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(data).decode()
    return f"data:{mime_type};base64,{encoded}"


def _call_local_model(image_data: bytes, mime_type: str, prompt: str) -> dict:
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
    response = local_client.chat.completions.create(
        model=model_cfg.name,
        messages=messages,
        **local_sampling_args,
        extra_body=local_extra_args,
    )
    end_at = datetime.datetime.now()

    return {
        "content": response.choices[0].message.content,
        "usage": response.usage.to_dict(),
        "latency": (end_at - start_at).total_seconds(),
    }


def _call_openrouter_model(
    model_name: str, image_data: bytes, mime_type: str, prompt: str
) -> dict:
    logger.info(f"调用 OpenRouter 模型: {model_name}")
    logger.info(f"图片大小: {len(image_data)} bytes, MIME类型: {mime_type}")
    logger.info(f"提示词长度: {len(prompt)} 字符")
    
    if not openrouter_client:
        error_msg = "OpenRouter 未启用或未配置 API Key"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _to_data_url(image_data, mime_type)}},
            ],
        }
    ]

    logger.info(f"请求参数: model={model_name}, sampling_args={openrouter_cfg.default_sampling_args}")
    logger.debug(f"Messages: {messages}")

    try:
        start_at = datetime.datetime.now()
        logger.info("开始调用 OpenRouter API...")
        response = openrouter_client.chat.completions.create(
            model=model_name,
            messages=messages,
            **openrouter_cfg.default_sampling_args,
        )
        end_at = datetime.datetime.now()
        latency = (end_at - start_at).total_seconds()
        
        logger.info(f"OpenRouter API 调用成功，延迟: {latency:.2f}s")
        logger.info(f"响应 usage: {response.usage}")
        
        result = {
            "content": response.choices[0].message.content,
            "usage": response.usage.to_dict(),
            "latency": latency,
        }
        logger.info(f"返回内容长度: {len(result['content'])} 字符")
        return result
    except Exception as e:
        logger.error(f"OpenRouter API 调用失败: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # 构建模型列表
    models = [{"id": "local", "name": model_cfg.name, "display_name": f"本地模型 ({model_cfg.name})"}]
    
    if openrouter_cfg.enabled:
        for or_model in openrouter_cfg.models:
            models.append({
                "id": f"openrouter:{or_model.name}",
                "name": or_model.name,
                "display_name": or_model.display_name,
            })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_prompt": DEFAULT_PROMPT,
            "default_model": models[0]["id"],
            "models": models,
            "openrouter_enabled": openrouter_cfg.enabled,
        },
    )


@app.post("/api/generate")
async def generate(
    prompt: str = Form(DEFAULT_PROMPT),
    model: str = Form("local"),
    file: UploadFile = File(...),
):
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
        prompt_text = prompt.strip() or DEFAULT_PROMPT
        logger.info(f"收到推理请求: model={model}, file_size={len(payload)} bytes, mime_type={mime_type}")
        
        # 根据模型选择调用不同的接口
        if model == "local":
            logger.info("使用本地模型")
            result = _call_local_model(payload, mime_type, prompt_text)
        elif model.startswith("openrouter:"):
            model_name = model.replace("openrouter:", "", 1)
            logger.info(f"使用 OpenRouter 模型: {model_name}")
            result = _call_openrouter_model(model_name, payload, mime_type, prompt_text)
        else:
            error_msg = f"不支持的模型: {model}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info("推理请求成功完成")
    except HTTPException:
        raise
    except Exception as exc:
        error_msg = f"推理请求失败: {type(exc).__name__}: {str(exc)}"
        logger.error(error_msg, exc_info=True)
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
    return {
        "status": "ok",
        "local_model": model_cfg.name,
        "openrouter_enabled": openrouter_cfg.enabled,
    }


