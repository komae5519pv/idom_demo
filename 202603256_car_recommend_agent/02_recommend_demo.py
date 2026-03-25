# Databricks notebook source
# MAGIC %md
# MAGIC # 02_recommend_demo - 車両提案AIデモ
# MAGIC
# MAGIC 商談録音テキストから顧客の**深層ニーズ**をAI抽出し、最適な車両を提案します。
# MAGIC
# MAGIC ## 処理フロー
# MAGIC ```
# MAGIC 入力: 顧客との商談録音テキスト（非構造化データ）
# MAGIC   ↓
# MAGIC AI分析: ライフステージ・価値観・隠れたニーズを深掘り
# MAGIC   ↓
# MAGIC マッチング: 顧客像に基づく車両スコアリング
# MAGIC   ↓
# MAGIC 出力: おすすめ車両 + 「なぜこの車があなたに最適か」のストーリー
# MAGIC ```
# MAGIC
# MAGIC > サーバレスコンピュートまたはSQLウェアハウスで実行してください

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定読み込み

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 顧客選択

# COMMAND ----------

# DBTITLE 1,顧客一覧
# MAGIC %sql
# MAGIC SELECT customer_id, customer_name, interaction_type, interaction_date
# MAGIC FROM customer_interactions
# MAGIC ORDER BY interaction_date DESC

# COMMAND ----------

# DBTITLE 1,対象顧客の選択
# 対象顧客を選択（デモ時に変更可能）
target_customer_id = "C001"  # C001: ファミリー層, C002: 単身者, C003: 高級志向

# 顧客情報を取得
customer_info = spark.sql(f"""
    SELECT * FROM customer_interactions
    WHERE customer_id = '{target_customer_id}'
""").collect()[0]

print(f"顧客ID: {customer_info['customer_id']}")
print(f"顧客名: {customer_info['customer_name']}")
print(f"商談タイプ: {customer_info['interaction_type']}")
print(f"商談日: {customer_info['interaction_date']}")

# COMMAND ----------

# DBTITLE 1,商談内容の確認
print("=" * 60)
print("商談録音テキスト")
print("=" * 60)
print(customer_info['transcript'])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 顧客インサイト分析（深層ニーズ抽出）
# MAGIC
# MAGIC 単なるスペック要件ではなく、会話の「行間」から顧客像を読み解きます。

# COMMAND ----------

# DBTITLE 1,顧客インサイト分析
import json
import re

# 深層ニーズ抽出プロンプト
insight_prompt = f"""あなたは熟練の自動車セールスコンサルタントです。
以下の商談会話から、顧客の**深層心理**と**本当のニーズ**を分析してください。

【商談会話】
{customer_info['transcript']}

以下のJSON形式で分析結果を出力してください。JSONのみを出力し、他の説明は不要です。

{{
  "customer_persona": {{
    "life_stage": "ライフステージ（例：子育て真っ最中の30代夫婦、定年退職後のアクティブシニア等）",
    "family_situation": "家族構成と状況の詳細",
    "lifestyle": "日常のライフスタイル・行動パターン",
    "values": "大切にしている価値観（安全、経済性、見栄、利便性等）",
    "personality": "会話から読み取れる性格・人柄"
  }},
  "deep_needs": {{
    "stated_needs": ["明示的に言葉にしたニーズ"],
    "unstated_needs": ["言葉にしていないが読み取れる潜在ニーズ"],
    "emotional_drivers": ["購買の感情的な動機（安心したい、家族を守りたい等）"],
    "concerns": ["本人が気にしている懸念点"],
    "hidden_concerns": ["口には出さないが気にしていそうな懸念"]
  }},
  "purchase_context": {{
    "trigger": "今回車を探し始めたきっかけ",
    "urgency": "購買の緊急度（高/中/低）と理由",
    "decision_factors": ["最終決定に影響する要素（価格、妻の意見、試乗感等）"],
    "budget_flexibility": "予算の柔軟性についての分析"
  }},
  "key_quotes": ["印象的な発言や本音が垣間見える発言を3つ抽出"],
  "ideal_car_profile": "この顧客に最適な車の特徴（スペックではなく、どんな体験を提供すべきか）"
}}
"""

insight_query = f"""
SELECT ai_query(
    'databricks-meta-llama-3-3-70b-instruct',
    '{insight_prompt.replace("'", "''")}'
) as customer_insight
"""

insight_result = spark.sql(insight_query).collect()[0]['customer_insight']

# JSONをパース
try:
    json_match = re.search(r'\{.*\}', insight_result, re.DOTALL)
    customer_insight = json.loads(json_match.group(0)) if json_match else {}
except Exception as e:
    print(f"パースエラー: {e}")
    customer_insight = {}

print("顧客インサイト分析完了")

# COMMAND ----------

# DBTITLE 1,インサイト詳細表示
import pprint
print("=" * 60)
print("顧客インサイト分析結果")
print("=" * 60)
pprint.pprint(customer_insight, width=80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 基本ニーズ抽出（マッチング用）

# COMMAND ----------

# DBTITLE 1,基本ニーズ抽出
# マッチング用の基本スペック抽出
basic_needs_prompt = f"""以下の商談テキストから車両マッチングに必要な基本情報を抽出してください。
JSONのみを出力してください。

商談テキスト:
{customer_info['transcript']}

{{
  "body_type": "希望ボディタイプ",
  "budget_min": 予算下限（円、整数）,
  "budget_max": 予算上限（円、整数）,
  "family_size": 家族人数,
  "primary_use": "主な用途",
  "must_have_features": ["必須機能"],
  "preferred_brands": ["好みのブランド（あれば）"],
  "deal_breakers": ["絶対NGな条件"]
}}
"""

needs_query = f"""
SELECT ai_query(
    'databricks-meta-llama-3-3-70b-instruct',
    '{basic_needs_prompt.replace("'", "''")}'
) as needs
"""

needs_result = spark.sql(needs_query).collect()[0]['needs']

try:
    json_match = re.search(r'\{.*\}', needs_result, re.DOTALL)
    needs = json.loads(json_match.group(0)) if json_match else {}
except:
    needs = {}

print("基本ニーズ:")
for k, v in needs.items():
    print(f"  {k}: {v}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 在庫車両とのマッチング

# COMMAND ----------

# DBTITLE 1,在庫車両取得とマッチング
# 基本フィルタリング
budget_min = needs.get('budget_min', 0) or 0
budget_max = needs.get('budget_max', 10000000) or 10000000
body_type = needs.get('body_type', '') or ''

# 在庫車両を取得
vehicles_df = spark.sql(f"""
    SELECT * FROM vehicle_inventory
    WHERE stock_status = '在庫あり'
    AND price BETWEEN {int(budget_min * 0.8)} AND {int(budget_max * 1.3)}
    ORDER BY price
""").collect()

print(f"候補車両: {len(vehicles_df)}台")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. AIによる車両マッチング＆ストーリー生成
# MAGIC
# MAGIC 顧客インサイトを踏まえて、**なぜこの車がこの人に最適なのか**をストーリーで語ります。

# COMMAND ----------

# DBTITLE 1,車両マッチング＆ストーリー生成
# 車両情報をテキスト化
vehicles_text = "\n".join([
    f"【{v['vehicle_id']}】{v['make']} {v['model']} {v['year']}年式\n"
    f"  価格: ¥{v['price']:,} / タイプ: {v['body_type']} / 燃料: {v['fuel_type']}\n"
    f"  定員: {v['seating_capacity']}人 / 特徴: {', '.join(v['features']) if v['features'] else 'なし'}"
    for v in vehicles_df
])

# マッチング＆ストーリー生成プロンプト
matching_prompt = f"""あなたは顧客の人生に寄り添う自動車セールスコンサルタントです。

【顧客インサイト】
{json.dumps(customer_insight, ensure_ascii=False, indent=2)}

【在庫車両リスト】
{vehicles_text}

この顧客に最適な車両TOP3を選び、以下のJSON形式で出力してください。

重要: 単なるスペックマッチではなく、「この車がこの人の人生をどう豊かにするか」というストーリーを語ってください。
顧客の発言や状況を引用しながら、共感と説得力のある提案理由を書いてください。

{{
  "recommendations": [
    {{
      "rank": 1,
      "vehicle_id": "車両ID",
      "match_score": 95,
      "headline": "この車を選ぶ一言キャッチコピー（顧客の心に刺さる一言）",
      "story": "なぜこの車がこの顧客に最適なのか、顧客のライフスタイル・価値観・懸念点に触れながら、200文字程度で説得力のあるストーリーを語る。顧客の発言を引用すると効果的。",
      "life_scene": "この車と過ごす具体的な生活シーン（週末の家族でのお出かけ、奥様の送り迎え等）を描写",
      "concern_resolution": "顧客の懸念（明示的・潜在的）にどう応えるか"
    }}
  ],
  "not_recommended": {{
    "vehicle_id": "あえて推奨しない車両ID（あれば）",
    "reason": "この顧客には合わない理由"
  }}
}}
"""

matching_query = f"""
SELECT ai_query(
    'databricks-meta-llama-3-3-70b-instruct',
    '{matching_prompt.replace("'", "''")}'
) as matching_result
"""

matching_result = spark.sql(matching_query).collect()[0]['matching_result']

try:
    json_match = re.search(r'\{.*\}', matching_result, re.DOTALL)
    recommendations_data = json.loads(json_match.group(0)) if json_match else {}
except Exception as e:
    print(f"パースエラー: {e}")
    recommendations_data = {"recommendations": []}

print("マッチング完了")

# COMMAND ----------

# DBTITLE 1,推奨結果の確認
recommendations = recommendations_data.get('recommendations', [])
for rec in recommendations:
    print(f"\n#{rec.get('rank', '?')} {rec.get('vehicle_id', '?')}")
    print(f"  見出し: {rec.get('headline', '')}")
    print(f"  スコア: {rec.get('match_score', 0)}%")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. 提案トークスクリプト生成

# COMMAND ----------

# DBTITLE 1,トークスクリプト生成
if recommendations:
    top_rec = recommendations[0]
    top_vehicle_id = top_rec.get('vehicle_id', '')
    top_vehicle = next((v for v in vehicles_df if v['vehicle_id'] == top_vehicle_id), vehicles_df[0] if vehicles_df else None)

    if top_vehicle:
        script_prompt = f"""あなたは顧客の心を掴むトップセールスです。

【顧客情報】
- 顧客名: {customer_info['customer_name']}様
- ライフステージ: {customer_insight.get('customer_persona', {}).get('life_stage', '不明')}
- 大切にしている価値観: {customer_insight.get('customer_persona', {}).get('values', '不明')}

【提案車両】
{top_vehicle['make']} {top_vehicle['model']} ¥{top_vehicle['price']:,}

【提案ストーリー】
{top_rec.get('story', '')}

【顧客の懸念】
{customer_insight.get('deep_needs', {}).get('concerns', [])}

上記を踏まえて、営業担当者が実際に使える自然な提案トークを150〜200文字で作成してください。
顧客の名前を呼び、共感を示し、具体的なベネフィットを伝えてください。
"""

        script_query = f"""
        SELECT ai_query(
            'databricks-meta-llama-3-3-70b-instruct',
            '{script_prompt.replace("'", "''")}'
        ) as script
        """

        talk_script = spark.sql(script_query).collect()[0]['script']
    else:
        talk_script = "車両情報が取得できませんでした。"
else:
    talk_script = "推奨車両がありません。"

print("トークスクリプト:")
print(talk_script)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. 結果表示

# COMMAND ----------

# DBTITLE 1,リッチな結果表示
import base64

def get_image_base64(image_path):
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except:
        return None

# 車両情報とレコメンデーションを結合
final_recommendations = []
for rec in recommendations[:3]:
    vehicle_id = rec.get('vehicle_id', '')
    vehicle = next((v for v in vehicles_df if v['vehicle_id'] == vehicle_id), None)
    if vehicle:
        final_recommendations.append({
            "rank": rec.get('rank', 0),
            "vehicle": vehicle,
            "headline": rec.get('headline', ''),
            "story": rec.get('story', ''),
            "life_scene": rec.get('life_scene', ''),
            "concern_resolution": rec.get('concern_resolution', ''),
            "match_score": rec.get('match_score', 80)
        })

# HTMLテンプレート
html_template = """
<style>
    .container {{
        font-family: 'Segoe UI', 'Hiragino Sans', sans-serif;
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
        background: #f5f7fa;
    }}
    .header {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        text-align: center;
    }}
    .header h1 {{
        margin: 0 0 10px 0;
        font-size: 2.2em;
    }}
    .header p {{
        margin: 0;
        opacity: 0.9;
    }}

    /* 顧客インサイトセクション */
    .insight-section {{
        background: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    .insight-section h2 {{
        color: #333;
        margin-top: 0;
        padding-bottom: 15px;
        border-bottom: 3px solid #667eea;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .insight-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 25px;
        margin-top: 20px;
    }}
    .insight-card {{
        background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #667eea;
    }}
    .insight-card h3 {{
        margin: 0 0 15px 0;
        color: #4a5568;
        font-size: 1em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .insight-card p {{
        margin: 0;
        color: #2d3748;
        line-height: 1.7;
    }}
    .persona-tag {{
        display: inline-block;
        background: #667eea;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        margin: 3px;
    }}
    .quote-box {{
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        padding: 15px 20px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #92400e;
    }}
    .quote-box::before {{
        content: '"';
        font-size: 2em;
        color: #f59e0b;
        line-height: 0;
        vertical-align: -0.3em;
        margin-right: 5px;
    }}

    /* 基本ニーズ */
    .needs-section {{
        background: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }}
    .needs-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 15px;
    }}
    .needs-item {{
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }}
    .needs-item label {{
        font-size: 0.8em;
        color: #718096;
        display: block;
        margin-bottom: 5px;
    }}
    .needs-item span {{
        font-weight: 600;
        color: #2d3748;
        font-size: 1.1em;
    }}

    /* 車両推奨セクション */
    .vehicles-section {{
        margin-bottom: 30px;
    }}
    .vehicles-section h2 {{
        color: #333;
        padding-bottom: 15px;
        border-bottom: 3px solid #667eea;
        margin-bottom: 25px;
    }}
    .vehicle-card {{
        background: white;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        display: grid;
        grid-template-columns: 350px 1fr;
        transition: transform 0.3s;
    }}
    .vehicle-card:hover {{
        transform: translateY(-5px);
    }}
    .vehicle-card.rank-1 {{
        border: 3px solid #FFD700;
    }}
    .vehicle-card.rank-2 {{
        border: 3px solid #C0C0C0;
    }}
    .vehicle-card.rank-3 {{
        border: 3px solid #CD7F32;
    }}
    .vehicle-image-container {{
        position: relative;
    }}
    .vehicle-image {{
        width: 100%;
        height: 250px;
        object-fit: cover;
    }}
    .rank-badge {{
        position: absolute;
        top: 15px;
        left: 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-weight: bold;
        font-size: 0.9em;
    }}
    .vehicle-content {{
        padding: 25px;
        display: flex;
        flex-direction: column;
    }}
    .vehicle-headline {{
        color: #667eea;
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 10px;
    }}
    .vehicle-name {{
        font-size: 1.5em;
        font-weight: bold;
        color: #1a202c;
        margin-bottom: 5px;
    }}
    .vehicle-price {{
        font-size: 1.8em;
        color: #e53e3e;
        font-weight: bold;
        margin-bottom: 10px;
    }}
    .vehicle-specs {{
        color: #718096;
        font-size: 0.9em;
        margin-bottom: 15px;
    }}
    .match-score {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 25px;
        font-weight: bold;
        margin-bottom: 15px;
    }}
    .story-section {{
        background: #f7fafc;
        padding: 20px;
        border-radius: 12px;
        margin-top: auto;
    }}
    .story-section h4 {{
        margin: 0 0 10px 0;
        color: #4a5568;
        font-size: 0.9em;
    }}
    .story-section p {{
        margin: 0;
        color: #2d3748;
        line-height: 1.8;
    }}
    .life-scene {{
        background: #ebf8ff;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        color: #2b6cb0;
        font-size: 0.95em;
    }}
    .life-scene::before {{
        content: '🚗 ';
    }}

    /* トークスクリプト */
    .script-section {{
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        color: white;
        padding: 30px;
        border-radius: 20px;
    }}
    .script-section h2 {{
        margin-top: 0;
        padding-bottom: 15px;
        border-bottom: 2px solid rgba(255,255,255,0.3);
    }}
    .script-content {{
        background: rgba(255,255,255,0.15);
        padding: 25px;
        border-radius: 15px;
        font-size: 1.1em;
        line-height: 1.9;
    }}
</style>

<div class="container">
    <div class="header">
        <h1>車両提案AI</h1>
        <p>顧客: {customer_name}様 | 商談日: {interaction_date}</p>
    </div>

    <div class="insight-section">
        <h2>🎯 顧客インサイト</h2>
        <div class="insight-grid">
            <div class="insight-card">
                <h3>ライフステージ & 価値観</h3>
                <p><strong>{life_stage}</strong></p>
                <p style="margin-top:10px">{values}</p>
                <div style="margin-top:15px">
                    {persona_tags}
                </div>
            </div>
            <div class="insight-card">
                <h3>潜在ニーズ（言葉にしていない本音）</h3>
                <p>{unstated_needs}</p>
                <p style="margin-top:10px; color:#667eea;"><strong>感情的な購買動機:</strong> {emotional_drivers}</p>
            </div>
        </div>
        <div style="margin-top:20px">
            <h3 style="color:#4a5568; margin-bottom:10px">💬 印象的な発言</h3>
            {key_quotes_html}
        </div>
    </div>

    <div class="needs-section">
        <h2 style="margin-top:0; margin-bottom:20px; color:#333;">📋 基本条件</h2>
        <div class="needs-grid">
            {needs_html}
        </div>
    </div>

    <div class="vehicles-section">
        <h2>🚘 あなたにおすすめの車両</h2>
        {vehicles_html}
    </div>

    <div class="script-section">
        <h2>💬 提案トークスクリプト</h2>
        <div class="script-content">
            {talk_script}
        </div>
    </div>
</div>
"""

# データ準備
persona = customer_insight.get('customer_persona', {})
deep_needs = customer_insight.get('deep_needs', {})

life_stage = persona.get('life_stage', '-')
values = persona.get('values', '-')
personality = persona.get('personality', '')
lifestyle = persona.get('lifestyle', '')

unstated_needs = ', '.join(deep_needs.get('unstated_needs', [])) or '-'
emotional_drivers = ', '.join(deep_needs.get('emotional_drivers', [])) or '-'

# ペルソナタグ
tags = []
if personality:
    tags.append(personality)
if lifestyle:
    tags.append(lifestyle[:20] + '...' if len(lifestyle) > 20 else lifestyle)
persona_tags = ''.join([f'<span class="persona-tag">{t}</span>' for t in tags[:3]])

# 印象的な発言
key_quotes = customer_insight.get('key_quotes', [])
key_quotes_html = ''.join([f'<div class="quote-box">{q}</div>' for q in key_quotes[:3]]) or '<p>-</p>'

# 基本ニーズHTML
def safe_get(d, key, default='-'):
    val = d.get(key) if isinstance(d, dict) else None
    return val if val is not None else default

def format_budget(d):
    bmin = d.get('budget_min') if isinstance(d, dict) else None
    bmax = d.get('budget_max') if isinstance(d, dict) else None
    if bmin and bmax:
        return f"¥{int(bmin):,} 〜 ¥{int(bmax):,}"
    return '-'

def format_list(d, key):
    val = d.get(key) if isinstance(d, dict) else None
    if isinstance(val, list):
        return ', '.join(str(v) for v in val) if val else '-'
    return str(val) if val else '-'

needs_items = [
    ("希望タイプ", safe_get(needs, 'body_type')),
    ("予算", format_budget(needs)),
    ("家族人数", f"{safe_get(needs, 'family_size')}人" if safe_get(needs, 'family_size') != '-' else '-'),
    ("主な用途", safe_get(needs, 'primary_use')),
    ("必須機能", format_list(needs, 'must_have_features')),
]
needs_html = ''.join([f'<div class="needs-item"><label>{label}</label><span>{value}</span></div>' for label, value in needs_items])

# 車両カードHTML
vehicles_html = ""
for rec in final_recommendations:
    v = rec['vehicle']
    rank = rec['rank']
    img_b64 = get_image_base64(v['image_path'])
    img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else "https://via.placeholder.com/350x250?text=No+Image"
    features_str = ', '.join(v['features'][:4]) if v['features'] else '-'

    vehicles_html += f"""
    <div class="vehicle-card rank-{rank}">
        <div class="vehicle-image-container">
            <img src="{img_src}" alt="{v['model']}" class="vehicle-image">
            <span class="rank-badge">#{rank} おすすめ</span>
        </div>
        <div class="vehicle-content">
            <div class="vehicle-headline">{rec['headline']}</div>
            <div class="vehicle-name">{v['make']} {v['model']}</div>
            <div class="vehicle-price">¥{v['price']:,}</div>
            <div class="vehicle-specs">{v['year']}年式 | {v['body_type']} | {v['fuel_type']} | {features_str}</div>
            <span class="match-score">✓ マッチ度 {rec['match_score']}%</span>
            <div class="story-section">
                <h4>なぜこの車があなたに最適か</h4>
                <p>{rec['story']}</p>
                <div class="life-scene">{rec['life_scene']}</div>
            </div>
        </div>
    </div>
    """

# 最終HTML生成
final_html = html_template.format(
    customer_name=customer_info['customer_name'],
    interaction_date=customer_info['interaction_date'],
    life_stage=life_stage,
    values=values,
    persona_tags=persona_tags,
    unstated_needs=unstated_needs,
    emotional_drivers=emotional_drivers,
    key_quotes_html=key_quotes_html,
    needs_html=needs_html,
    vehicles_html=vehicles_html,
    talk_script=talk_script
)

displayHTML(final_html)

# COMMAND ----------

# MAGIC %md
# MAGIC ## デモ完了
# MAGIC
# MAGIC ### このデモが示すDatabricksの価値
# MAGIC
# MAGIC | 機能 | 活用方法 |
# MAGIC |------|----------|
# MAGIC | **AI Functions** | 非構造化テキストから顧客の深層心理を抽出 |
# MAGIC | **Foundation Model API** | 顧客インサイト分析・ストーリー生成・トークスクリプト作成 |
# MAGIC | **Unity Catalog** | 顧客・車両データのガバナンス |
# MAGIC | **Delta Lake** | 商談履歴・在庫データの管理 |
# MAGIC
# MAGIC ### 従来のシステムとの違い
# MAGIC
# MAGIC | 従来 | Databricks + AI |
# MAGIC |------|-----------------|
# MAGIC | キーワード検索・完全一致 | 文脈を理解した意味マッチング |
# MAGIC | スペック条件フィルタ | 顧客の価値観・ライフスタイルを考慮 |
# MAGIC | 定型文の提案理由 | 顧客ごとにパーソナライズされたストーリー |
# MAGIC | 営業の経験・勘に依存 | AIが「行間を読む」サポート |
