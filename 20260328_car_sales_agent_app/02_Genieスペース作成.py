# Databricks notebook source
# MAGIC %md
# MAGIC # IDOM Car AI - Genieスペース作成
# MAGIC
# MAGIC ## 1. Genie Spaceを作る
# MAGIC
# MAGIC カタログエクスプローラーからテーブルを選択し「Genieスペースを作成」をクリック
# MAGIC
# MAGIC ![Genieスペース作成.gif](./_gifs/Genieスペース作成.gif "Genieスペース作成.gif")
# MAGIC
# MAGIC
# MAGIC ### 登録するテーブル
# MAGIC
# MAGIC | テーブル名 | 説明 |
# MAGIC |-----------|------|
# MAGIC | `komae_demo_v4.idom_car_ai.customers` | 顧客マスタ（年齢・職業・家族構成・予算・重視点など） |
# MAGIC | `komae_demo_v4.idom_car_ai.vehicle_inventory` | 車両在庫（メーカー・モデル・年式・価格・ボディタイプ・燃料・装備など） |
# MAGIC | `komae_demo_v4.idom_car_ai.customer_interactions` | 商談録音・テキスト（商談日・担当者・書き起こし） |
# MAGIC | `komae_demo_v4.idom_car_ai.customer_insights` | 顧客インサイト（ペルソナ要約・深層ニーズ・購買緊急度など） |
# MAGIC | `komae_demo_v4.idom_car_ai.recommendations` | 推薦実績（推薦車両・スコア・トークスクリプト・生成日） |
# MAGIC
# MAGIC ### 設定内容
# MAGIC
# MAGIC - **Title**: `IDOM 車両営業アシスタント`
# MAGIC - **Description**: `IDOM営業チーム向けの顧客・在庫データ分析アシスタント。顧客の予算・家族構成・重視ポイントと車両在庫を照合し、最適提案を支援します。商談履歴・推薦実績も参照可能。`
# MAGIC - **Default Warehouse**: <任意のSQL Warehouse>
# MAGIC
# MAGIC ### サンプル質問
# MAGIC
# MAGIC ```
# MAGIC 予算280万円以内でSUVを希望している顧客を教えて
# MAGIC ```
# MAGIC
# MAGIC ```
# MAGIC ハイブリッド車で在庫あり、価格300万円以下の車両を一覧で見せて
# MAGIC ```
# MAGIC
# MAGIC ```
# MAGIC 田中 翔太さんの予算と希望条件に合う在庫車両を絞り込んで
# MAGIC ```
# MAGIC
# MAGIC ### 一般的な指示（General Instructions）
# MAGIC
# MAGIC ```
# MAGIC あなたはIDOMの自動車営業支援アシスタントです。
# MAGIC 営業担当者が顧客への最適提案・商談準備・在庫確認をスムーズに行えるよう、データに基づいたサポートをしてください。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 1. 分析の基本姿勢
# MAGIC
# MAGIC 顧客データを参照する際は、単なるフィルタ検索ではなく、
# MAGIC 「この顧客の生活背景・家族構成・仕事スタイルから、何を本当に求めているか」を読み取ってください。
# MAGIC
# MAGIC ### 主なテーブルと活用方法
# MAGIC
# MAGIC | テーブル | 主要カラム | 活用方法 |
# MAGIC |---------|-----------|---------|
# MAGIC | customers | age, family_structure, occupation, budget_min/max, preferences, background | 顧客ニーズの把握・ターゲティング |
# MAGIC | vehicle_inventory | make, model, price, body_type, fuel_type, features | 条件マッチング・在庫確認 |
# MAGIC | customer_interactions | transcript, interaction_date, key_quotes | 商談内容・顧客発言の確認 |
# MAGIC | customer_insights | persona_summary, deep_needs, purchase_urgency | 深層ニーズ・購買意欲の把握 |
# MAGIC | recommendations | recommendations_json, talk_script, generated_at | 過去の推薦内容・スコア確認 |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 2. よく使う分析パターン
# MAGIC
# MAGIC ### 顧客×在庫マッチング
# MAGIC customers.budget_min/max と vehicle_inventory.price を照合し、
# MAGIC customers.preferences（例：「SUV希望」「安全装備重視」）と vehicle_inventory.body_type / features を照合。
# MAGIC
# MAGIC ### 商談準備サポート
# MAGIC customer_interactions.transcript から顧客の発言・懸念点を抽出し、
# MAGIC customer_insights.deep_needs と組み合わせて提案方針を整理。
# MAGIC
# MAGIC ### 推薦実績の確認
# MAGIC recommendations テーブルから過去の推薦内容・スコアを参照し、
# MAGIC 「前回と比べて何が変わったか」「どの車がよく推薦されているか」を分析。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 3. 必須ルール
# MAGIC
# MAGIC 1. **日本語で回答**
# MAGIC 2. **顧客名・車名は正確に**（略称・誤字を避ける）
# MAGIC 3. **価格は「万円」表記**（例：228万円）
# MAGIC 4. **在庫なし・該当なしの場合は明示**
# MAGIC 5. **複数条件がある場合はすべて満たす候補を優先**し、なければ条件緩和候補を提示
# MAGIC 6. **次のアクション提案**（例：「この顧客に試乗を提案するのはいかがでしょう」）
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 4. 利用可能テーブル一覧
# MAGIC
# MAGIC | テーブル | 説明 | 主な用途 |
# MAGIC |---------|------|---------|
# MAGIC | customers | 顧客マスタ | 属性・予算・ニーズ把握 |
# MAGIC | vehicle_inventory | 車両在庫 | 在庫確認・条件マッチ |
# MAGIC | customer_interactions | 商談録音テキスト | 発言・懸念点の確認 |
# MAGIC | customer_insights | 顧客インサイト | 深層ニーズ・購買意欲 |
# MAGIC | recommendations | 推薦実績 | 過去の推薦内容確認 |
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Genie Spaceに権限を付与する
# MAGIC
# MAGIC デモ用に `all workspace users` に権限を付与
# MAGIC
# MAGIC 1. Genieスペースの右上「共有」をクリック
# MAGIC 2. `all workspace users` を追加
# MAGIC 3. 権限レベル: `Can query`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Genieスペース ID を控える
# MAGIC
# MAGIC 後のマルチエージェントスーパーバイザー設定で使用します。
# MAGIC
# MAGIC URLの `genie/spaces/` 以降の文字列がGenieスペースIDです。
# MAGIC
# MAGIC 例: `https://e2-demo-field-eng.cloud.databricks.com/genie/spaces/**xxxxxxxxxxxxxxxxx**`
# MAGIC
# MAGIC ```
# MAGIC # ここにGenieスペースIDをメモしておく
# MAGIC GENIE_SPACE_ID = "xxxxxxxxxxxxxxxxx"
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. デモの流れ（Genieスペース単体テスト）
# MAGIC
# MAGIC ### Lv1 基本的な在庫・顧客確認
# MAGIC
# MAGIC | 質問 | 期待される回答 |
# MAGIC |------|--------------|
# MAGIC | 現在の在庫車両を一覧で見せて | 全10台の一覧（メーカー・モデル・価格・ボディタイプ） |
# MAGIC | 予算250万円以内でSUVの在庫は？ | ヴェゼル（265万）が近い、フリード（205万）はミニバンなど絞り込み結果 |
# MAGIC | 田中 翔太さんの家族構成と予算は？ | 独身・彼女あり、予算150〜280万円 |
# MAGIC
# MAGIC ### Lv2 顧客×在庫マッチング
# MAGIC
# MAGIC | 質問 | 期待される回答 |
# MAGIC |------|--------------|
# MAGIC | 田中さんの予算内でSUVに絞ったら何が残る？ | ヴェゼル（265万）、フリード（205万）など条件マッチ結果 |
# MAGIC | 渡辺 雅子さんの重視点と予算に合う車を3台推薦して | 安全性・積載・ステータス重視、400〜600万円。NX・XC40・3シリーズなど |
# MAGIC | 全顧客の中で今すぐ商談を進めやすいのは誰？purchase_urgencyを見て | customer_insightsのpurchase_urgencyが高い顧客 |
# MAGIC
# MAGIC ### Lv3 集計・傾向分析
# MAGIC
# MAGIC | 質問 | 期待される回答 |
# MAGIC |------|--------------|
# MAGIC | 在庫車両の平均価格は？ボディタイプ別に見せて | SUV平均・ミニバン平均・セダン平均の比較 |
# MAGIC | 顧客の予算分布を見せて（予算帯ごとに何人いる？） | 150〜300万・300〜450万・450万以上 の顧客数 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. テーブル間の関係
# MAGIC
# MAGIC ```
# MAGIC customers (PK: customer_id)
# MAGIC   │
# MAGIC   ├── customer_interactions (FK: customer_id) ── 商談録音・テキスト
# MAGIC   ├── customer_insights (FK: customer_id) ────── 深層ニーズ分析結果
# MAGIC   └── recommendations (FK: customer_id) ──────── 推薦車両・トークスクリプト
# MAGIC
# MAGIC vehicle_inventory (PK: vehicle_id)
# MAGIC   └── recommendations.recommendations_json ────── 推薦結果にvehicle_idで紐付き
# MAGIC ```
# MAGIC
# MAGIC ### 重要なカラム
# MAGIC
# MAGIC | テーブル | 重要カラム | 用途 |
# MAGIC |---------|-----------|------|
# MAGIC | customers | budget_min, budget_max, preferences, background | 予算・ニーズ把握 |
# MAGIC | vehicle_inventory | price, body_type, fuel_type, features, status | 在庫マッチング |
# MAGIC | customer_insights | persona_summary, deep_needs, purchase_urgency | 購買意欲判断 |
# MAGIC | customer_interactions | transcript, key_quotes | 商談内容確認 |
# MAGIC | recommendations | recommendations_json, talk_script, generated_at | 推薦実績確認 |
