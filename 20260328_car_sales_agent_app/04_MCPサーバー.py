# Databricks notebook source
# MAGIC %md
# MAGIC # IDOM Car AI - MCPサーバー（Tavily Web Search）
# MAGIC
# MAGIC [MCPサーバー接続の作成](https://docs.databricks.com/aws/ja/generative-ai/agent-framework/mcp-server-connections.html)
# MAGIC
# MAGIC Web上の最新情報（車種レビュー・競合比較・維持費情報など）を検索するために
# MAGIC Tavily MCP Serverをセットアップします。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Tavily MCP Serverをインストールする
# MAGIC
# MAGIC 1. [https://app.tavily.com](https://app.tavily.com) でユーザーアカウント作成後、**Tavily API Key** を取得
# MAGIC    - 無料プランで月1,000リクエスト利用可能
# MAGIC 2. **Marketplace** を開く
# MAGIC 3. 「Tavily」で検索
# MAGIC 4. **Tavily MCP Server** を選択 → 「Install」でインストール
# MAGIC 5. MCP接続を作成
# MAGIC
# MAGIC | 項目 | 値 | 備考 |
# MAGIC |------|-----|------|
# MAGIC | 接続名 | `tavily_search` | このまま使用（マルチエージェントと名前を合わせる） |
# MAGIC | ホスト | `https://mcp.tavily.com` | 固定 |
# MAGIC | ベースパス | `/mcp` | 固定 |
# MAGIC | ベアラートークン | `<あなたのTavily API Key>` | [https://app.tavily.com](https://app.tavily.com) から取得 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 接続を確認する

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE CONNECTION tavily_search;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. IDOM用ユースケース：Web検索で何を調べるか
# MAGIC
# MAGIC Tavilyを使うのは、社内データ（Genie）でも社内ナレッジ（RAG）でもカバーできない情報が必要な場合です。
# MAGIC
# MAGIC ### 主な活用シーン
# MAGIC
# MAGIC | シーン | 検索クエリ例 |
# MAGIC |--------|------------|
# MAGIC | 競合他社の最新価格 | 「ホンダ ヴェゼル 2024年式 価格」 |
# MAGIC | カーメディアのレビュー・評価 | 「シエンタ vs フリード 2024 比較 評価」 |
# MAGIC | 最新モデルのリコール・不具合情報 | 「ハリアー 2023 リコール情報」 |
# MAGIC | 車のランキング・口コミ | 「SUV 人気ランキング 2024」 |
# MAGIC | ローン金利・残クレ最新動向 | 「マイカーローン 金利 2024 最新」 |
# MAGIC | 電気自動車・次世代車の動向 | 「2024 日本 EVシフト 中古車市場」 |
# MAGIC
# MAGIC > **注意**: 在庫・顧客データ・社内ルールはGenieまたはRAGで取得してください。
# MAGIC > Web検索はあくまで「社外の最新情報」の補完に使います。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. マルチエージェントスーパーバイザーに追加する
# MAGIC
# MAGIC `05_AgentBricksマルチエージェントスーパーバイザー` のエージェント設定で、
# MAGIC MCPサーバーとして `tavily_search` を追加する（次のノートブックへ）
