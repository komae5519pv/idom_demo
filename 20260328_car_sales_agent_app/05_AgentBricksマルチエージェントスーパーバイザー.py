# Databricks notebook source
# MAGIC %md
# MAGIC # IDOM Car AI - マルチエージェントスーパーバイザー
# MAGIC
# MAGIC [Agent Bricksの使用: Multi-Agent Supervisor](https://docs.databricks.com/aws/ja/generative-ai/agent-bricks/multi-agent-supervisor)
# MAGIC
# MAGIC Genie（構造化データ）・ナレッジアシスタント（RAG）・Tavily（Web検索）を統合し、
# MAGIC 営業担当者のあらゆる質問に対応するスーパーバイザーを構築します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. マルチエージェントスーパーバイザーを作る
# MAGIC
# MAGIC - Agent Bricks → マルチエージェントスーパーバイザー → ビルド
# MAGIC - **名前**: `idom-car-ai-assistant`
# MAGIC - **説明**: `IDOM自動車営業チーム向けの総合AIアシスタント。顧客データ・在庫・推薦実績（Genie）、車両スペック・営業トーク・金融知識（RAG）、Web最新情報（Tavily）を統合し、商談準備から提案・クロージングまで一貫してサポートします。`
# MAGIC
# MAGIC ### エージェントを設定
# MAGIC
# MAGIC | タイプ | エージェント | エージェント名 | 説明 |
# MAGIC |--------|-------------|--------------|------|
# MAGIC | Genieスペース | `IDOM 車両営業アシスタント`（02で作成したGenieスペース） | agent | customers・vehicle_inventory・customer_interactions・customer_insights・recommendationsテーブルを参照し、顧客プロフィール・在庫状況・商談履歴・推薦実績などの構造化データを検索・分析するエージェント |
# MAGIC | ナレッジアシスタント | `idom-car-knowledge-bot`（03で作成したKA） | agent | 車両カタログ・スペック、営業トーク集・商談ガイド、維持費・ローン・保険の基礎知識を参照し、商談準備・顧客提案・金融アドバイスを支援するナレッジアシスタント |
# MAGIC | MCPサーバー | `tavily_search`（04で作成したMCP接続） | — | Web上の最新情報（最新モデル・競合価格・口コミ・業界動向）を検索する。社内データやナレッジに含まれない外部情報が必要な場合に使用。 |
# MAGIC
# MAGIC ### 手順設定（オプション）
# MAGIC
# MAGIC ```
# MAGIC * あなたはIDOMの自動車営業チームを支援するAIアシスタントです
# MAGIC * 必ず日本語で回答してください
# MAGIC * 顧客の呼び方は必ず「苗字＋様」（例：渡辺様、山田様）。下の名前では呼ばない
# MAGIC
# MAGIC * エージェントの使い分け（ルーティング基準）:
# MAGIC   - 「Genie（IDOM 車両営業アシスタント）」: 顧客の予算・家族構成・ニーズ、在庫車両の絞り込み、商談履歴・発言の確認、推薦実績の確認など、テーブルから取得する事実データが必要な場合
# MAGIC   - 「ナレッジアシスタント（idom-car-knowledge-bot）」: 車両スペック比較・燃費・装備の詳細、営業トーク・クロージング手法、維持費・ローン・保険の説明方法など、カタログ・マニュアルに基づくナレッジが必要な場合
# MAGIC   - 「Tavily（Web検索）」: 最新モデルの市場評価・口コミ、競合他社の価格動向、リコール情報、業界トレンドなど、社内データ・ナレッジにない外部最新情報が必要な場合
# MAGIC   - 複数のエージェントが必要な場合は必ずすべて使用する
# MAGIC
# MAGIC * 最初に結論を簡潔に述べ、その後に詳細を説明してください
# MAGIC
# MAGIC * 最終回答は以下の順で整理してください（該当する項目のみ）:
# MAGIC   1. 顧客・在庫データ（事実）
# MAGIC   2. 車両知識・スペック・ナレッジ
# MAGIC   3. 外部情報（Web検索結果、必要な場合のみ）
# MAGIC   4. 営業担当者へのアクション提案
# MAGIC   5. 顧客向けトーク例（必要な場合）
# MAGIC
# MAGIC * 商談準備の質問を受けた場合は:
# MAGIC   - Genieで顧客の予算・家族構成・インサイトを確認し
# MAGIC   - RAGで該当車両のスペック・トークポイントを参照して
# MAGIC   - 「この顧客にはこう話すと刺さる」という具体的なトーク例まで出してください
# MAGIC
# MAGIC * 車両比較の質問を受けた場合は:
# MAGIC   - RAGでスペック・装備・価格帯を比較表形式で整理し
# MAGIC   - 必要に応じてTavilyで最新の市場評価も追加してください
# MAGIC
# MAGIC * 在庫確認の質問を受けた場合は:
# MAGIC   - Genieで条件（予算・ボディタイプ・燃料など）に合う在庫を絞り込み
# MAGIC   - RAGで各車のセールスポイントを補足してください
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ![マルチエージェントスーパーバイザー作成.gif](./_gifs/マルチエージェントスーパーバイザー作成.gif "マルチエージェントスーパーバイザー作成.gif")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. マルチエージェントスーパーバイザーを使ってみる
# MAGIC
# MAGIC | 質問番号 | 質問内容 | 主な参照エージェント | 狙い |
# MAGIC |---------|---------|------------------|------|
# MAGIC | Q1 | 田中 翔太さんの希望条件と予算を教えて。その条件で在庫に合う車は何がある？ | Genie | 顧客データ取得→在庫マッチング。Genie単体の動作確認 |
# MAGIC | Q2 | ヴェゼルとフリードを比較して。安全装備と維持費の違いを整理して | RAG（catalogs + finance） | RAGの車両スペック比較と金融知識の組み合わせ確認 |
# MAGIC | Q3 | ヴェゼルの最新モデル、Web上の評判はどう？口コミや専門家レビューを調べて | Tavily | Web検索エージェントの動作確認 |
# MAGIC | Q4 | 田中さんに今日試乗を提案したい。どう話しかければいい？ | Genie + RAG | 顧客データ（Genie）とトーク知識（RAG）の統合。★最大の見せ場 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. スーパーバイザーのエンドポイントを確認する
# MAGIC
# MAGIC デプロイ後、アプリから呼び出すためのエンドポイント情報を控えます。
# MAGIC
# MAGIC Agent Bricks → マルチエージェントスーパーバイザー → `idom-car-ai-assistant` → 「デプロイ」タブ
# MAGIC
# MAGIC - **エンドポイント名**: `idom-car-ai-assistant-xxxxxxxx`（自動生成）
# MAGIC - **エンドポイントURL**: `https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/idom-car-ai-assistant-xxxxxxxx/invocations`
# MAGIC
# MAGIC ```python
# MAGIC # アプリのchat.pyで使用する設定値
# MAGIC AGENT_ENDPOINT_NAME = "idom-car-ai-assistant-xxxxxxxx"
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. アプリとの接続
# MAGIC
# MAGIC アプリの `app/backend/app/routers/chat.py` でこのエンドポイントを呼び出すよう設定します。
# MAGIC
# MAGIC ### エンドポイントの呼び出し方
# MAGIC
# MAGIC ```python
# MAGIC import httpx
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC
# MAGIC async def call_agent(message: str, customer_id: str, conversation_history: list) -> str:
# MAGIC     """マルチエージェントスーパーバイザーを呼び出す"""
# MAGIC     client = WorkspaceClient()
# MAGIC     token = client.config.token
# MAGIC     host = client.config.host
# MAGIC
# MAGIC     # 顧客コンテキストをシステムメッセージとして注入
# MAGIC     system_context = f"現在表示中の顧客ID: {customer_id}。この顧客に関する質問には必ずこのIDで顧客データを参照してください。"
# MAGIC
# MAGIC     payload = {
# MAGIC         "messages": [
# MAGIC             {"role": "system", "content": system_context},
# MAGIC             *conversation_history,
# MAGIC             {"role": "user", "content": message}
# MAGIC         ]
# MAGIC     }
# MAGIC
# MAGIC     async with httpx.AsyncClient(timeout=60.0) as http:
# MAGIC         resp = await http.post(
# MAGIC             f"{host}/serving-endpoints/{AGENT_ENDPOINT_NAME}/invocations",
# MAGIC             json=payload,
# MAGIC             headers={"Authorization": f"Bearer {token}"}
# MAGIC         )
# MAGIC         result = resp.json()
# MAGIC         return result["choices"][0]["message"]["content"]
# MAGIC ```
# MAGIC
# MAGIC > **ポイント**: 顧客ページからチャットする場合、`customer_id` をシステムメッセージに含めることで
# MAGIC > 「今見ている顧客の田中さんに〜」という質問が正確にルーティングされます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. アプリのサービスプリンシパルに権限を付与する
# MAGIC
# MAGIC **⚠️ これを忘れるとアプリのチャットがレスポンスを返しません（ハマりポイント）**
# MAGIC
# MAGIC Databricks Apps はアプリ専用のサービスプリンシパル（SP）で動作します。
# MAGIC そのSPがエンドポイントを呼び出す権限を持っていないと、チャットリクエストが403エラーになります。
# MAGIC
# MAGIC ### 手順
# MAGIC
# MAGIC 1. Apps → `idom-car-ai` → **「許可」タブ** でサービスプリンシパル名を確認（例: `app-40zbx9 idom-car-ai`）
# MAGIC 2. **Serving Endpoints** → エンドポイント名（例: `mas-c850699f-endpoint`）を開く
# MAGIC 3. 右上の「**Permissions**」ボタンをクリック
# MAGIC 4. 「Add permission」→ 検索欄に上記で確認したSP名（`app-XXXXXXXX idom-car-ai`）を入力
# MAGIC 5. 表示されたサービスプリンシパルを選択 → **`Can Query`** を付与 → 保存

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Playgroundでテストする
# MAGIC
# MAGIC 本格接続の前に、Agent Bricks の Playground で動作確認することをおすすめします。
# MAGIC
# MAGIC Agent Bricks → `idom-car-ai-assistant` → 「Playground」タブ
# MAGIC
# MAGIC ### 動作確認チェックリスト
# MAGIC
# MAGIC - [ ] Genieが顧客データ・在庫を正しく取得できる
# MAGIC - [ ] RAGが車両スペック・トーク例を返せる
# MAGIC - [ ] Tavilyが最新情報を取得できる
# MAGIC - [ ] 複合質問で複数エージェントを使い分けられる
# MAGIC - [ ] 顧客の呼び方が苗字+様になっている
# MAGIC - [ ] 回答が日本語で出力されている
