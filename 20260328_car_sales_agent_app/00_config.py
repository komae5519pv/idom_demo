# Databricks notebook source
# MAGIC %md
# MAGIC # 00_config - IDOM Car AI 設定
# MAGIC
# MAGIC このノートブックでは、デモに必要なUnity Catalog環境（カタログ、スキーマ、ボリューム）をセットアップします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定パラメータ

# COMMAND ----------

# 基本設定
CATALOG = "komae_demo_v4"
SCHEMA = "idom_car_ai"
VOLUME_NAME = "images"

# LLM設定
LLM_MODEL = "databricks-claude-sonnet-4"

# フルパス
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_NAME}"

print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}")
print(f"Full Schema Path: {FULL_SCHEMA}")
print(f"Volume Path: {VOLUME_PATH}")
print(f"LLM Model: {LLM_MODEL}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Unity Catalog セットアップ

# COMMAND ----------

# カタログが存在することを確認（既存を使用）
spark.sql(f"USE CATALOG {CATALOG}")
print(f"✓ Using catalog: {CATALOG}")

# COMMAND ----------

# スキーマを作成（存在しない場合）
spark.sql(f"""
    CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}
    COMMENT 'IDOM Car AI デモ用スキーマ - 車両推薦AIエージェント'
""")
print(f"✓ Schema created/verified: {FULL_SCHEMA}")

# COMMAND ----------

# ボリュームを作成（車両画像格納用）
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME_NAME}
    COMMENT '車両画像を格納するボリューム'
""")
print(f"✓ Volume created/verified: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## テーブル定義

# COMMAND ----------

# 顧客テーブル
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {FULL_SCHEMA}.customers (
        customer_id STRING COMMENT '顧客ID',
        name STRING COMMENT '氏名',
        age INT COMMENT '年齢',
        gender STRING COMMENT '性別',
        occupation STRING COMMENT '職業',
        address STRING COMMENT '住所',
        family_structure STRING COMMENT '家族構成',
        current_vehicle STRING COMMENT '現在の車',
        budget_min INT COMMENT '予算下限',
        budget_max INT COMMENT '予算上限',
        preferences STRING COMMENT '好み・要望',
        background STRING COMMENT '背景情報（詳細）',
        created_at TIMESTAMP COMMENT '登録日時'
    )
    USING DELTA
    COMMENT '顧客マスタテーブル'
""")
print(f"✓ Table created/verified: {FULL_SCHEMA}.customers")

# COMMAND ----------

# 車両在庫テーブル
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {FULL_SCHEMA}.vehicle_inventory (
        vehicle_id STRING COMMENT '車両ID',
        make STRING COMMENT 'メーカー',
        model STRING COMMENT '車種',
        year INT COMMENT '年式',
        price INT COMMENT '価格（税込）',
        body_type STRING COMMENT 'ボディタイプ',
        fuel_type STRING COMMENT '燃料タイプ',
        mileage INT COMMENT '走行距離',
        color STRING COMMENT 'カラー',
        features ARRAY<STRING> COMMENT '特徴・装備',
        image_path STRING COMMENT '画像パス',
        description STRING COMMENT '説明文',
        status STRING COMMENT 'ステータス（在庫あり/商談中/売約済）',
        created_at TIMESTAMP COMMENT '登録日時'
    )
    USING DELTA
    COMMENT '車両在庫テーブル'
""")
print(f"✓ Table created/verified: {FULL_SCHEMA}.vehicle_inventory")

# COMMAND ----------

# 商談録音テーブル（Bronzeレイヤー）
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {FULL_SCHEMA}.customer_interactions (
        interaction_id STRING COMMENT '商談ID',
        customer_id STRING COMMENT '顧客ID',
        interaction_date DATE COMMENT '商談日',
        interaction_type STRING COMMENT '種類（来店/電話/オンライン）',
        sales_rep STRING COMMENT '担当営業',
        transcript STRING COMMENT '音声認識テキスト（生データ）',
        duration_minutes INT COMMENT '商談時間（分）',
        created_at TIMESTAMP COMMENT '登録日時'
    )
    USING DELTA
    COMMENT '商談録音テキスト（Bronze）'
""")
print(f"✓ Table created/verified: {FULL_SCHEMA}.customer_interactions")

# COMMAND ----------

# AIインサイトテーブル（Silverレイヤー）
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {FULL_SCHEMA}.customer_insights (
        insight_id STRING COMMENT 'インサイトID',
        customer_id STRING COMMENT '顧客ID',
        interaction_id STRING COMMENT '関連する商談ID',
        persona_summary STRING COMMENT 'ペルソナ要約',
        deep_needs ARRAY<STRING> COMMENT '深層ニーズ',
        key_quotes ARRAY<STRING> COMMENT '印象的な発言',
        concerns ARRAY<STRING> COMMENT '懸念事項',
        preferences_extracted STRING COMMENT '抽出された好み',
        life_stage STRING COMMENT 'ライフステージ',
        purchase_urgency STRING COMMENT '購入緊急度',
        confidence_score FLOAT COMMENT 'AI分析の確信度',
        processed_at TIMESTAMP COMMENT '処理日時',
        model_used STRING COMMENT '使用したLLMモデル'
    )
    USING DELTA
    COMMENT 'AIで抽出した顧客インサイト（Silver）'
""")
print(f"✓ Table created/verified: {FULL_SCHEMA}.customer_insights")

# COMMAND ----------

# 推薦結果テーブル（Goldレイヤー）
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {FULL_SCHEMA}.recommendations (
        recommendation_id STRING COMMENT '推薦ID',
        customer_id STRING COMMENT '顧客ID',
        vehicle_id STRING COMMENT '推薦車両ID',
        rank INT COMMENT '推薦順位',
        match_score FLOAT COMMENT 'マッチスコア（0-100）',
        headline STRING COMMENT 'キャッチコピー',
        reason STRING COMMENT '推薦理由（営業向け）',
        customer_benefit STRING COMMENT '顧客へのベネフィット',
        talk_points ARRAY<STRING> COMMENT 'トークポイント',
        created_at TIMESTAMP COMMENT '生成日時',
        model_used STRING COMMENT '使用したLLMモデル'
    )
    USING DELTA
    COMMENT 'AI生成の車両推薦（Gold）'
""")
print(f"✓ Table created/verified: {FULL_SCHEMA}.recommendations")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定完了確認

# COMMAND ----------

# テーブル一覧表示
tables = spark.sql(f"SHOW TABLES IN {FULL_SCHEMA}").collect()
print(f"\n=== {FULL_SCHEMA} のテーブル一覧 ===")
for t in tables:
    print(f"  - {t.tableName}")

# ボリューム確認
volumes = spark.sql(f"SHOW VOLUMES IN {FULL_SCHEMA}").collect()
print(f"\n=== {FULL_SCHEMA} のボリューム一覧 ===")
for v in volumes:
    print(f"  - {v.volume_name}")

print("\n✅ セットアップ完了!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 次のステップ
# MAGIC
# MAGIC セットアップが完了したら、`01_setup_demo_data` ノートブックを実行してデモデータを投入してください。
