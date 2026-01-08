"""聊天业务服务。"""

from __future__ import annotations

import datetime as dt
import logging
import secrets
from typing import Optional, List

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.models.user import ModelConfig, Role, RolePrompt, User
from app.schemas.message import ChatCompletionRequest
from app.services.memory_service import (
    search_memories,
    extract_and_save_memory,
    is_memory_enabled,
)

logger = logging.getLogger(__name__)


def _get_all_models(session: Session) -> List[ModelConfig]:
    """获取所有可用模型"""
    return list(session.exec(select(ModelConfig)).all())


def _select_model(session: Session, payload: ChatCompletionRequest) -> ModelConfig:
    model: Optional[ModelConfig] = None
    if payload.model_id:
        model = session.get(ModelConfig, payload.model_id)
    if not model:
        model = session.exec(select(ModelConfig)).first()
    if not model:
        raise HTTPException(status_code=404, detail="尚未配置可用模型")
    return model


def _role_prompt(session: Session, payload: ChatCompletionRequest) -> Optional[str]:
    role_prompt_text = payload.role_prompt
    if payload.role_id:
        prompt_record = session.get(RolePrompt, payload.role_id)
        if not prompt_record:
            raise HTTPException(status_code=404, detail="提示词不存在")
        role_prompt_text = prompt_record.prompt
    if not role_prompt_text:
        fallback_prompt = session.exec(select(RolePrompt).order_by(RolePrompt.id)).first()
        if fallback_prompt:
            role_prompt_text = fallback_prompt.prompt
    return role_prompt_text


def build_chat_request(
    session: Session,
    payload: ChatCompletionRequest,
    user: User,
) -> tuple[ModelConfig, str, dict, List[ModelConfig]]:
    model = _select_model(session, payload)
    if model.owner_id and user.role != Role.admin.value and user.id != model.owner_id:
        raise HTTPException(status_code=403, detail="无权使用该模型")

    # 获取备用模型（排除当前模型和用户无权使用的模型）
    all_models = _get_all_models(session)
    fallback_models = [
        m for m in all_models 
        if m.id != model.id and (not m.owner_id or user.role == Role.admin.value or user.id == m.owner_id)
    ]

    # 如果 base_url 已包含 /chat/completions 则直接使用，否则拼接
    if 'chat/completions' in model.base_url:
        target_url = model.base_url
    else:
        target_url = f"{model.base_url.rstrip('/')}/chat/completions"
    system_prompts = [
        {
            "role": "system",
            "content": f"当前用户昵称：{user.name}，角色：{user.role}。请在回答时体现礼貌、简洁并结合用户身份。",
        }
    ]

    # 获取用户相关记忆
    if is_memory_enabled() and payload.messages:
        last_user_msg = None
        for msg in reversed(payload.messages):
            if msg.role == "user":
                last_user_msg = msg.content
                break
        
        if last_user_msg:
            memories = search_memories(last_user_msg, str(user.id), limit=3)
            if memories:
                memory_context = "用户相关记忆：\n" + "\n".join(f"- {m}" for m in memories)
                system_prompts.append({
                    "role": "system",
                    "content": memory_context,
                })

    role_prompt_text = _role_prompt(session, payload)
    if role_prompt_text:
        system_prompts.append({"role": "system", "content": role_prompt_text})

    merged_messages = [*system_prompts, *[msg.model_dump() for msg in payload.messages]]
    request_body = {
        "model": model.model_name,
        "messages": merged_messages,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
    }
    if payload.stream:
        request_body["stream"] = True

    return model, target_url, request_body, fallback_models


def stream_chat_completion(model: ModelConfig, target_url: str, request_body: dict, fallback_models: List[ModelConfig] = None) -> StreamingResponse:
    """流式聊天，支持模型故障转移"""
    
    def try_model(m: ModelConfig, url: str, body: dict):
        """尝试单个模型"""
        body_copy = body.copy()
        body_copy["model"] = m.model_name
        
        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                url,
                headers={"Authorization": f"Bearer {m.api_key}"},
                json=body_copy,
            ) as upstream_response:
                if upstream_response.status_code >= 400:
                    error_bytes = upstream_response.read()
                    error_text = error_bytes.decode("utf-8", errors="replace")
                    try:
                        error_body = upstream_response.json()
                        error_text = error_body.get("error", {}).get("message", error_text)
                    except ValueError:
                        pass
                    return upstream_response.status_code, error_text, None
                
                # 成功，返回响应迭代器
                chunks = list(upstream_response.iter_text())
                return 200, None, chunks
        
    def stream_response():
        # 尝试主模型
        models_to_try = [model] + (fallback_models or [])
        last_error = None
        last_status = 500
        
        for i, m in enumerate(models_to_try):
            try:
                # 如果 base_url 已包含 /chat/completions 则直接使用，否则拼接
                if 'chat/completions' in m.base_url:
                    url = m.base_url
                else:
                    url = f"{m.base_url.rstrip('/')}/chat/completions"
                status, error, chunks = try_model(m, url, request_body)
                
                if status == 200 and chunks:
                    if i > 0:
                        logger.info(f"模型 {model.name} 失败，已切换到备用模型 {m.name}")
                    for chunk in chunks:
                        if chunk:
                            yield chunk
                    return
                
                # 记录错误
                last_status = status
                last_error = error
                
                # 429/502/503 错误尝试下一个模型
                if status in (429, 502, 503) and i < len(models_to_try) - 1:
                    logger.warning(f"模型 {m.name} 返回 {status}，尝试下一个模型")
                    continue
                    
            except httpx.RequestError as exc:
                last_error = str(exc)
                last_status = 502
                if i < len(models_to_try) - 1:
                    logger.warning(f"模型 {m.name} 请求失败: {exc}，尝试下一个模型")
                    continue
        
        # 所有模型都失败
        if "Moderation" in (last_error or "") or "moderation" in (last_error or "").lower():
            last_error = "内容被安全审核拦截，请修改消息内容后重试"
        raise HTTPException(status_code=last_status, detail=f"上游错误：{last_error}")

    return StreamingResponse(stream_response(), media_type="text/event-stream")


def fetch_chat_completion(model: ModelConfig, target_url: str, request_body: dict) -> dict:
    try:
        with httpx.Client(timeout=30.0) as client:
            upstream_response = client.post(
                target_url,
                headers={"Authorization": f"Bearer {model.api_key}"},
                json=request_body,
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"请求上游模型失败：{exc}") from exc

    if upstream_response.status_code >= 400:
        try:
            error_body = upstream_response.json()
            error_message = error_body.get("error", {}).get("message", upstream_response.text)
        except ValueError:
            error_message = upstream_response.text
        raise HTTPException(status_code=upstream_response.status_code, detail=f"上游错误：{error_message}")

    data = upstream_response.json()
    now_ts = int(dt.datetime.now().timestamp())
    data.setdefault("id", f"chatcmpl-{secrets.token_hex(6)}")
    data.setdefault("object", "chat.completion")
    data.setdefault("created", now_ts)
    data.setdefault("model", model.model_name)
    data.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    return data
