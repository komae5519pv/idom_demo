# Databricks notebook source
# MAGIC %md
# MAGIC # 00_config - IDOM Car AI 共通設定
# MAGIC
# MAGIC デモ全体で共通利用する設定値・パス変数を定義します。
# MAGIC 各ノートブックの先頭で `%run ./00_config` を実行してください。

# COMMAND ----------

# 基本設定
CATALOG = "komae_demo_v4"
SCHEMA = "idom_car_ai"

# LLM設定
LLM_MODEL = "databricks-claude-sonnet-4"

# 派生パス
FULL_SCHEMA = f"{CATALOG}.{SCHEMA}"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/images"
KA_VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/knowledge"
WORKSPACE_BASE = "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent"

print(f"✓ CATALOG        : {CATALOG}")
print(f"✓ SCHEMA         : {SCHEMA}")
print(f"✓ VOLUME_PATH    : {VOLUME_PATH}")
print(f"✓ KA_VOLUME_PATH : {KA_VOLUME_PATH}")
print(f"✓ LLM_MODEL      : {LLM_MODEL}")

# COMMAND ----------

# カタログ・スキーマ・ボリュームのセットアップ
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA} COMMENT 'IDOM Car AI デモ用スキーマ'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.images COMMENT '車両画像格納用ボリューム'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.knowledge COMMENT 'ナレッジアシスタント用ドキュメント格納場所'")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

print(f"✓ Schema/Volumes ready: {FULL_SCHEMA}")
