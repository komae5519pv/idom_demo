"""Vehicle recommendation API endpoints with demo data support."""

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.database import db
from app.llm import llm
from app.models import (
    Vehicle,
    VehicleRecommendation,
    RecommendationResponse,
    APIResponse,
)
from app.config import get_full_table_name
from app.demo_data import (
    get_demo_customer,
    get_demo_recommendations,
    get_demo_talk_script,
    get_demo_vehicles_for_customer,
    get_demo_interaction,
    DEMO_VEHICLES,
)

router = APIRouter(prefix="/api", tags=["recommendations"])

# Use demo data when DEMO_MODE is set or database is not configured
USE_DEMO = os.getenv("DEMO_MODE", "true").lower() == "true"


@router.get("/vehicles", response_model=APIResponse)
async def list_vehicles(
    limit: int = 20,
    offset: int = 0,
    body_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
) -> APIResponse:
    """Get list of available vehicles."""
    try:
        if USE_DEMO:
            vehicles = DEMO_VEHICLES.copy()

            # Apply filters
            if body_type:
                vehicles = [v for v in vehicles if v["body_type"] == body_type]
            if min_price:
                vehicles = [v for v in vehicles if v["price"] >= min_price]
            if max_price:
                vehicles = [v for v in vehicles if v["price"] <= max_price]

            # Apply pagination
            vehicles = vehicles[offset : offset + limit]

            return APIResponse(success=True, data=vehicles)

        # Use database
        table = get_full_table_name("vehicles")
        conditions = []

        if body_type:
            conditions.append(f"body_type = '{body_type}'")
        if min_price:
            conditions.append(f"price >= {min_price}")
        if max_price:
            conditions.append(f"price <= {max_price}")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM {table}
            WHERE {where_clause}
            LIMIT {limit} OFFSET {offset}
        """

        results = await db.execute_query(query)
        return APIResponse(success=True, data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/recommendations", response_model=APIResponse)
async def get_recommendations(customer_id: str) -> APIResponse:
    """Get vehicle recommendations for a customer."""
    try:
        if USE_DEMO:
            # Get pre-defined recommendations
            recommendations = get_demo_recommendations(customer_id)
            talk_script = get_demo_talk_script(customer_id)

            if recommendations:
                # Enrich recommendations with vehicle objects
                vehicle_map = {v['vehicle_id']: v for v in DEMO_VEHICLES}
                enriched_recs = []
                for rec in recommendations:
                    vehicle = vehicle_map.get(rec['vehicle_id'])
                    if vehicle:
                        enriched_recs.append({
                            "vehicle": vehicle,
                            "match_score": rec['match_score'],
                            "reason": rec['reason'],
                            "headline": rec.get('headline'),
                            "life_scene": rec.get('life_scene'),
                        })

                result = {
                    "customer_id": customer_id,
                    "recommendations": enriched_recs,
                    "talk_script": talk_script,
                }
                return APIResponse(success=True, data=result)

        # Get customer data
        if USE_DEMO:
            customer = get_demo_customer(customer_id)
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            vehicle_results = get_demo_vehicles_for_customer(customer_id)
            interaction = get_demo_interaction(customer_id)
        else:
            customers_table = get_full_table_name("customers")
            customer_query = f"SELECT * FROM {customers_table} WHERE customer_id = '{customer_id}'"
            customer_results = await db.execute_query(customer_query)

            if not customer_results:
                raise HTTPException(status_code=404, detail="Customer not found")

            customer = customer_results[0]

            # Get available vehicles
            vehicles_table = get_full_table_name("vehicles")
            vehicles_query = f"""
                SELECT * FROM {vehicles_table}
                WHERE price BETWEEN {customer['budget_min']} AND {customer['budget_max']}
                LIMIT 20
            """
            vehicle_results = await db.execute_query(vehicles_query)

            if not vehicle_results:
                # Fallback to all vehicles if none in budget
                vehicles_query = f"SELECT * FROM {vehicles_table} LIMIT 20"
                vehicle_results = await db.execute_query(vehicles_query)

            interaction = None

        # Generate recommendations using LLM
        vehicles_info = "\n".join([
            f"- {v['vehicle_id']}: {v['make']} {v['model']} ({v['year']}年) - {v['price']:,}円 - {v['body_type']} - {v['fuel_type']} - 特徴: {', '.join(v.get('features', []))}"
            for v in vehicle_results
        ])

        # Include transcript if available
        transcript_context = ""
        if interaction and interaction.get("transcript"):
            transcript_context = f"""
商談録音テキスト（重要な文脈情報）:
{interaction['transcript']}

この商談内容から読み取れる顧客の深層ニーズも考慮して推薦してください。
"""

        prompt = f"""以下の顧客に最適な車両を3台推薦してください。

顧客情報:
- 名前: {customer['name']}
- 年齢: {customer['age']}歳
- 職業: {customer.get('occupation', '不明')}
- 家族構成: {customer.get('family_structure', '不明')}
- 予算: {customer.get('budget_min', 0):,}円 〜 {customer.get('budget_max', 0):,}円
- 好み: {customer.get('preferences', 'なし')}
{transcript_context}
利用可能な車両:
{vehicles_info}

以下のJSON形式で回答してください。match_scoreは0-100の整数で。
reasonは顧客の発言やニーズに具体的に言及した、営業担当者が使える説得力のある文章にしてください。
{{
    "recommendations": [
        {{"vehicle_id": "V001", "match_score": 95, "reason": "具体的な推薦理由..."}},
        {{"vehicle_id": "V002", "match_score": 88, "reason": "具体的な推薦理由..."}},
        {{"vehicle_id": "V003", "match_score": 82, "reason": "具体的な推薦理由..."}}
    ]
}}"""

        messages = [
            {"role": "system", "content": "あなたは自動車販売のエキスパートです。顧客の深層ニーズを理解し、最適な車両を推薦してください。推薦理由は、営業担当者が顧客に話せる具体的で説得力のある文章にしてください。"},
            {"role": "user", "content": prompt}
        ]

        response = await llm.chat(messages)

        # Parse recommendations
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            rec_data = json.loads(json_str.strip())

            # Build recommendation response
            recommendations = []
            vehicle_map = {v['vehicle_id']: v for v in vehicle_results}

            for rec in rec_data.get("recommendations", [])[:3]:
                vehicle_data = vehicle_map.get(rec['vehicle_id'])
                if vehicle_data:
                    recommendations.append({
                        "vehicle": vehicle_data,
                        "match_score": rec['match_score'],
                        "reason": rec['reason']
                    })
        except (json.JSONDecodeError, KeyError, IndexError):
            # Fallback to first 3 vehicles
            recommendations = [
                {
                    "vehicle": v,
                    "match_score": 85 - i * 10,
                    "reason": f"{v['make']} {v['model']}は予算内で良い選択です。"
                }
                for i, v in enumerate(vehicle_results[:3])
            ]

        # Generate talk script
        talk_script = await _generate_talk_script(customer, recommendations, interaction)

        result = {
            "customer_id": customer_id,
            "recommendations": recommendations,
            "talk_script": talk_script
        }

        return APIResponse(success=True, data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_talk_script(
    customer: dict,
    recommendations: list[dict],
    interaction: Optional[dict] = None
) -> str:
    """Generate talk script for the recommendations."""
    vehicles_info = "\n".join([
        f"- {rec['vehicle']['make']} {rec['vehicle']['model']}: マッチ度{rec['match_score']}% - {rec['reason']}"
        for rec in recommendations
    ])

    # Include key quotes from interaction if available
    key_quotes_context = ""
    if interaction and interaction.get("key_quotes"):
        quotes = "\n".join([f'「{q}」' for q in interaction["key_quotes"]])
        key_quotes_context = f"""
顧客の印象的な発言:
{quotes}

これらの発言を踏まえ、共感を示しながら提案するトークを作成してください。
"""

    transcript_context = ""
    if interaction and interaction.get("transcript"):
        transcript_context = f"""
商談録音テキスト:
{interaction['transcript'][:2000]}
"""

    prompt = f"""以下の顧客と推薦車両に基づき、営業トークスクリプトを生成してください。

顧客情報:
- 名前: {customer['name']}
- 年齢: {customer['age']}歳
- 職業: {customer.get('occupation', '不明')}
- 家族構成: {customer.get('family_structure', '不明')}
{key_quotes_context}
{transcript_context}
推薦車両:
{vehicles_info}

以下の構成でスクリプトを作成してください:
## {customer['name']}様へのご提案トーク

### 導入
（自然な挨拶）

### 共感ポイント
（顧客の発言や気持ちへの共感）

### ご提案
（車両紹介と具体的なベネフィット）

### クロージング
（次のアクションへの誘導）

Markdown形式で、実際に営業担当者が使える自然な日本語で出力してください。"""

    messages = [
        {"role": "system", "content": "あなたは経験豊富な自動車営業担当者です。顧客の気持ちに寄り添い、共感を示しながら自然に提案できるトークスクリプトを作成してください。堅苦しくなく、でもプロフェッショナルな印象を与える文体で。"},
        {"role": "user", "content": prompt}
    ]

    return await llm.chat(messages)


@router.post("/customers/{customer_id}/recommendations/regenerate", response_model=APIResponse)
async def regenerate_recommendations(
    customer_id: str,
    feedback: Optional[str] = None
) -> APIResponse:
    """Regenerate recommendations with optional feedback."""
    # This would incorporate feedback into the prompt
    # For now, just call the regular recommendation endpoint
    return await get_recommendations(customer_id)
