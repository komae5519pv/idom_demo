"""Chat API endpoints - RAG-powered with Unity Catalog data."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.database import db
from app.llm import llm
from app.models import ChatRequest, ChatResponse, APIResponse
from app.config import get_full_table_name

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory chat history
chat_sessions: dict[str, list[dict]] = {}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a chat message and get a RAG-powered response."""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        # Initialize session if new
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            system_prompt = await _build_system_prompt(customer_id)
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

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
            system_prompt = await _build_system_prompt(customer_id)
            chat_sessions[session_id].append({
                "role": "system",
                "content": system_prompt
            })

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


async def _build_system_prompt(customer_id: Optional[str]) -> str:
    """Build RAG-augmented system prompt with customer context from Unity Catalog."""

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

    if not customer_id:
        return base_prompt

    # RAG: Unity Catalogから顧客データを取得してコンテキストに組み込む
    try:
        context_sections = []

        # 1. 顧客プロフィール（customersテーブル）
        customers_table = get_full_table_name("customers")
        customer_rows = await db.execute_query(
            f"SELECT * FROM {customers_table} WHERE customer_id = '{customer_id}' LIMIT 1"
        )
        if customer_rows:
            c = customer_rows[0]
            context_sections.append(f"""
【顧客プロフィール】(Unity Catalog: customers テーブル)
- 氏名: {c.get('name', '不明')}（{c.get('age', '?')}歳・{c.get('gender', '')}）
- 職業: {c.get('occupation', '不明')}
- 住所: {c.get('address', '不明')}
- 家族構成: {c.get('family_structure', '不明')}
- 現在の車: {c.get('current_vehicle', 'なし')}
- 予算: {int(c.get('budget_min', 0)):,}円 〜 {int(c.get('budget_max', 0)):,}円
- 希望・好み: {c.get('preferences', 'なし')}
- 背景情報: {c.get('background', 'なし')}""")

        # 2. 商談録音テキスト（customer_interactionsテーブル）
        interactions_table = get_full_table_name("customer_interactions")
        interaction_rows = await db.execute_query(
            f"""SELECT * FROM {interactions_table}
                WHERE customer_id = '{customer_id}'
                ORDER BY interaction_date DESC
                LIMIT 1"""
        )
        if interaction_rows:
            i = interaction_rows[0]
            transcript = i.get('transcript', '')
            # 商談録音テキストは長いので最初の3000文字に絞る
            transcript_excerpt = transcript[:3000] + '...' if len(transcript) > 3000 else transcript
            context_sections.append(f"""
【最新商談録音テキスト】(Unity Catalog: customer_interactions テーブル)
- 商談日: {i.get('interaction_date', '不明')}
- 種類: {i.get('interaction_type', '不明')}
- 担当営業: {i.get('sales_rep', '不明')}
- 商談時間: {i.get('duration_minutes', '?')}分
- 録音テキスト（音声認識）:
{transcript_excerpt}""")

        # 3. AIインサイト（customer_insightsテーブル・存在する場合）
        try:
            insights_table = get_full_table_name("customer_insights")
            insight_rows = await db.execute_query(
                f"""SELECT * FROM {insights_table}
                    WHERE customer_id = '{customer_id}'
                    ORDER BY processed_at DESC
                    LIMIT 1"""
            )
            if insight_rows:
                ins = insight_rows[0]
                context_sections.append(f"""
【AI分析インサイト】(Unity Catalog: customer_insights テーブル)
- ペルソナ要約: {ins.get('persona_summary', 'なし')}
- 深層ニーズ: {ins.get('deep_needs', [])}
- 主な懸念事項: {ins.get('concerns', [])}
- ライフステージ: {ins.get('life_stage', '不明')}
- 購入緊急度: {ins.get('purchase_urgency', '不明')}""")
        except Exception:
            pass  # インサイトテーブルがなくても続行

        if context_sections:
            context_text = "\n".join(context_sections)
            return f"""{base_prompt}

=== RAG取得データ（Unity Catalogより） ===
{context_text}

===========================================
上記の顧客情報と商談録音テキストを踏まえ、この顧客に最適なアドバイスや情報を提供してください。
顧客の発言（録音テキスト）に基づいた具体的な回答を心がけてください。"""

    except Exception as e:
        print(f"RAG context retrieval failed: {e} - using basic prompt")

    return base_prompt + f"\n\n現在対応中の顧客ID: {customer_id}"
