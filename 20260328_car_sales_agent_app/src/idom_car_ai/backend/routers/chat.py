"""Chat API endpoints - Multi-Agent Supervisor経由."""

import asyncio
import json
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from idom_car_ai.backend.models import ChatRequest, ChatResponse, APIResponse
from idom_car_ai.backend.config import get_settings, get_oauth_token, get_databricks_host

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory chat history (セッションIDごと)
chat_sessions: dict[str, list[dict]] = {}


async def _call_agent_raw(messages: list[dict]) -> dict:
    """マルチエージェントスーパーバイザーエンドポイントを呼び出し、フル結果dictを返す。"""
    settings = get_settings()
    host = get_databricks_host()
    token = get_oauth_token()

    if not host or not token:
        return {"_no_connection": True}

    url = f"{host}/serving-endpoints/{settings.agent_endpoint_name}/invocations"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            url,
            json={"input": messages},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


def _extract_progress_and_answer(output: list) -> tuple[list[str], str]:
    """outputリストからプログレスメッセージと最終回答を抽出する。"""
    progress_list: list[str] = []
    final_answer = ""

    for item in output:
        item_type = item.get("type")

        if item_type == "function_call":
            progress_list.append("ツールを呼び出し中...")

        elif item_type == "message" and item.get("role") == "assistant":
            # テキストを取得
            text = ""
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    text = content["text"]
                    break

            if not text:
                continue

            # ルーティングメッセージの判定: <name>で始まる、または非常に短く(<80文字)<で始まる
            is_routing = text.startswith("<name>") or (len(text) < 80 and text.strip().startswith("<"))

            if text.startswith("<name>idom-car-knowledge-bot</name>"):
                progress_list.append("ナレッジベース（車両知識）を検索中...")
            elif text.startswith("<name>idom-car-ai-assistant</name>") or "Genie" in text:
                progress_list.append("社内データ（Genie）を検索中...")
            elif "<name>tavily" in text.lower():
                progress_list.append("Web検索中...")
            elif text.startswith("<name>"):
                progress_list.append("エージェントに問い合わせ中...")
            elif not is_routing:
                # 非ルーティングメッセージ = 最終回答候補
                final_answer = text

    return progress_list, final_answer


def _build_system_message(customer_id: Optional[str]) -> dict:
    """顧客コンテキストを含むシステムメッセージを生成する。"""
    content = "現在、営業担当者向けのIDOM Car AIアシスタントとして動作しています。"
    if customer_id:
        content += f"\n\n現在表示中の顧客ID: {customer_id}。この顧客に関する質問には必ずこのIDで顧客データを参照してください。"
    return {"role": "system", "content": content}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """チャットメッセージを送信してエージェントから回答を得る。"""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        # 会話履歴にユーザーメッセージを追加
        chat_sessions[session_id].append({"role": "user", "content": message})

        # システムメッセージ + 会話履歴をエージェントに送信
        messages = [_build_system_message(customer_id)] + chat_sessions[session_id]
        result = await _call_agent_raw(messages)

        if result.get("_no_connection"):
            response = "デモモード: エージェントエンドポイントに接続できません。"
        else:
            _, response = _extract_progress_and_answer(result.get("output", []))
            if not response:
                # OpenAI互換形式のフォールバック
                try:
                    response = result["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    response = ""

        # アシスタント応答を履歴に保存
        chat_sessions[session_id].append({"role": "assistant", "content": response})

        return ChatResponse(session_id=session_id, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """エージェント呼び出しをSSEストリームとして返す（エージェントはnon-streaming）。"""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        chat_sessions[session_id].append({"role": "user", "content": message})
        messages = [_build_system_message(customer_id)] + chat_sessions[session_id]

        async def generate():
            try:
                result = await _call_agent_raw(messages)

                if result.get("_no_connection"):
                    yield f"data: {json.dumps({'type': 'content', 'content': 'デモモード: エージェントエンドポイントに接続できません。'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                progress_list, final_answer = _extract_progress_and_answer(result.get("output", []))

                # プログレスメッセージを送信
                for msg in progress_list:
                    yield f"data: {json.dumps({'type': 'progress', 'message': msg})}\n\n"

                # 最終回答をチャンク分割してSSEで送信
                if not final_answer:
                    # OpenAI互換形式のフォールバック
                    try:
                        final_answer = result["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        final_answer = ""

                chat_sessions[session_id].append({"role": "assistant", "content": final_answer})

                chunk_size = 30
                for i in range(0, len(final_answer), chunk_size):
                    chunk = final_answer[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.02)

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=APIResponse)
async def get_chat_history(session_id: str) -> APIResponse:
    """セッションのチャット履歴を返す。"""
    if session_id not in chat_sessions:
        return APIResponse(success=True, data=[])

    history = [msg for msg in chat_sessions[session_id] if msg["role"] != "system"]
    return APIResponse(success=True, data=history)


@router.delete("/history/{session_id}", response_model=APIResponse)
async def clear_chat_history(session_id: str) -> APIResponse:
    """セッションのチャット履歴を削除する。"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return APIResponse(success=True, data={"message": "Chat history cleared"})
