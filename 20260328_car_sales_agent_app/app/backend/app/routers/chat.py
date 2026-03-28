"""Chat API endpoints with streaming support."""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import db
from app.llm import llm
from app.models import ChatRequest, ChatResponse, APIResponse
from app.config import get_full_table_name

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory chat history (in production, use database)
chat_sessions: dict[str, list[dict]] = {}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a chat message and get a response."""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

            # Add system prompt with customer context if available
            system_prompt = _build_system_prompt(customer_id)
            chat_sessions[session_id].append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message to history
        chat_sessions[session_id].append({
            "role": "user",
            "content": message
        })

        # Get response from LLM
        response = await llm.chat(chat_sessions[session_id])

        # Add assistant response to history
        chat_sessions[session_id].append({
            "role": "assistant",
            "content": response
        })

        return ChatResponse(session_id=session_id, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Send a chat message and get a streaming response."""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            system_prompt = _build_system_prompt(customer_id)
            chat_sessions[session_id].append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message
        chat_sessions[session_id].append({
            "role": "user",
            "content": message
        })

        async def generate():
            full_response = ""
            try:
                stream = await llm.chat(chat_sessions[session_id], stream=True)
                async for chunk in stream:
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

                # Save full response to history
                chat_sessions[session_id].append({
                    "role": "assistant",
                    "content": full_response
                })

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=APIResponse)
async def get_chat_history(session_id: str) -> APIResponse:
    """Get chat history for a session."""
    if session_id not in chat_sessions:
        return APIResponse(success=True, data=[])

    # Filter out system messages
    history = [
        msg for msg in chat_sessions[session_id]
        if msg["role"] != "system"
    ]

    return APIResponse(success=True, data=history)


@router.delete("/history/{session_id}", response_model=APIResponse)
async def clear_chat_history(session_id: str) -> APIResponse:
    """Clear chat history for a session."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]

    return APIResponse(success=True, data={"message": "Chat history cleared"})


def _build_system_prompt(customer_id: Optional[str]) -> str:
    """Build system prompt with optional customer context."""
    base_prompt = """あなたはIDOMの車両販売AIアシスタントです。
以下の役割を担っています:

1. 顧客の質問に丁寧に回答する
2. 車両に関する専門知識を提供する
3. 顧客のニーズに合った提案をサポートする
4. 営業担当者の質問にも対応する

回答のガイドライン:
- 簡潔で分かりやすい日本語を使用
- 具体的な数字や事実に基づいた回答
- 顧客目線での提案
- 不明な点は正直に「確認が必要」と伝える"""

    if customer_id:
        base_prompt += f"\n\n現在対応中の顧客ID: {customer_id}"

    return base_prompt
