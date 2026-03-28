# IDOM Car AI - アーキテクチャ仕様書

## 概要

IDOM Car AI は、中古車販売店向けの AI アシスタント Databricks App です。
顧客の商談録音から嗜好を分析し、最適な車両をレコメンドします。

---

## 現在の状態（2026年3月28日）

**本番モードで稼働中**

- Unity Catalog テーブル作成済み・デモデータ投入済み
- Foundation Model API（databricks-claude-sonnet-4）でリアルなLLM応答
- AIチャットはRAGで UCテーブルから顧客コンテキストを取得して回答
- App URL: https://idom-car-ai-1444828305810485.aws.databricksapps.com/

---

## デモモード vs 本番モード

### 切り替えの仕組み

```
┌─────────────────────────────────────────────────────────────┐
│  DATABRICKS_WAREHOUSE_ID が設定されている？                  │
│     YES → Unity Catalog に接続（本番モード）                 │
│     NO  → デモモードで起動（ハードコードされたデータを使用）  │
└─────────────────────────────────────────────────────────────┘
```

### データソース対照表

| データ種別 | デモモード | 本番モード |
|-----------|-----------|-----------|
| 顧客データ | `demo_data.py` | `komae_demo_v4.idom_car_ai.customers` |
| 車両在庫 | `demo_data.py` | `komae_demo_v4.idom_car_ai.vehicle_inventory` |
| 商談録音 | `demo_data.py` | `komae_demo_v4.idom_car_ai.customer_interactions` |
| 顧客インサイト | `demo_data.py` | `komae_demo_v4.idom_car_ai.customer_insights` |
| LLM応答 | ハードコード | Foundation Model API (claude-sonnet-4) |
| AIチャット | ハードコード | RAG + Foundation Model API |

---

## Unity Catalog 構成

### カタログ / スキーマ

```
komae_demo_v4
  └── idom_car_ai
        ├── customers              # 顧客プロフィール
        ├── vehicle_inventory      # 車両在庫
        ├── customer_interactions  # 商談録音テキスト（Bronze）
        ├── customer_insights      # AIインサイト（Silver）
        └── recommendations        # 推薦結果（Gold）
```

### 投入済みデモデータ

| テーブル | 件数 | 内容 |
|---------|------|------|
| `customers` | 4名 | 山田優子(C001)・佐藤健一(C002)・田中翔太(C003)・渡辺雅子(C004) |
| `vehicle_inventory` | 10台 | シエンタ・フリード・ヴェゼル・ハリアー・プリウス・レクサスNX・ボルボXC40・アルファード・フォレスター・BMW3シリーズ |
| `customer_interactions` | 4件 | 各顧客の来店商談録音テキスト（リアルな話し言葉） |
| `customer_insights` | 4件 | 深層ニーズ・購入緊急度・キーフレーズ |

---

## app.yaml（現在の設定）

```yaml
command: ['python', 'app/backend/run.py']

env:
  - name: 'DATABRICKS_WAREHOUSE_ID'
    value: '03560442e95cb440'      # my_warehouse (Small, RUNNING)

  - name: 'CATALOG'
    value: 'komae_demo_v4'
  - name: 'SCHEMA_NAME'
    value: 'idom_car_ai'

  - name: 'LLM_MODEL'
    value: 'databricks-claude-sonnet-4'

  - name: 'DEBUG'
    value: 'false'
  - name: 'DEMO_MODE'
    value: 'false'
```

---

## バックエンド構成

### 関連ファイル

```
app/backend/app/
├── config.py             # 設定（catalog, schema, warehouse等）
├── database.py           # Databricks SDK Statement Execution API で UCクエリ
├── llm.py                # Foundation Model API クライアント（MLflowトレース付き）
├── demo_data.py          # フォールバック用ハードコードデータ
└── routers/
    ├── customers.py      # 顧客CRUD + インサイト取得
    ├── recommendations.py # LLMによる車両推薦 + トークスクリプト生成
    ├── chat.py           # RAG付きAIチャット
    └── admin.py          # LLMOps管理画面
```

### database.py の実装方針

Databricks SDK の `statement_execution.execute_statement()` を使用。
（旧: `databricks-sql-connector` → 認証トークン取得の問題でSDK方式に変更）

```python
response = self._client.statement_execution.execute_statement(
    warehouse_id=self._warehouse_id,
    statement=query,
    wait_timeout="30s",
)
```

### chat.py の RAG 実装

チャット開始時（新セッション）に UC から顧客コンテキストを取得してシステムプロンプトに注入：

1. `customers` テーブル → 顧客プロフィール・背景・予算
2. `customer_interactions` テーブル → 最新商談録音テキスト（直近1件）
3. `customer_insights` テーブル → AI分析インサイト（存在する場合）

これにより「山田様のお義母様（72歳）が乗り降りしやすい車種は...」のような個別化された回答が可能。

---

## LLMOps 機能（管理者画面）

| 機能 | 説明 |
|------|------|
| ダッシュボード | KPI概要（推論数、レイテンシ、エラー率） |
| MLflow Traces | LLM呼び出しのトレーシング（`@mlflow.trace`デコレーター） |
| Evaluations | LLM-as-Judge 評価（Relevance・Faithfulness・Helpfulness） |
| Data Catalog | UC テーブル一覧（実テーブルへのリンク） |

---

## フロントエンド構成

- React 19 + TypeScript 5.9 + TailwindCSS 4 + Vite

```
/                    → 顧客一覧
/customers/:id       → 顧客詳細 + レコメンド + トークスクリプト + AIチャット
/admin               → LLMOps管理画面
```

---

## デプロイ手順

### フロントエンドビルド & デプロイ

```bash
# フロントエンドビルド
cd app/frontend
npm run build

# dist をコピー（重要！FastAPIはapp/dist/をserveする）
rm -rf ../dist && cp -r dist ../dist

# デプロイ
cd ../..
databricks apps deploy idom-car-ai \
  --source-code-path "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent" \
  --mode SNAPSHOT
```

### バックエンドのみ変更した場合

```bash
# ファイルをワークスペースにimportしてからデプロイ
databricks workspace import /path/in/workspace --file /local/file --format AUTO --overwrite
databricks apps deploy idom-car-ai \
  --source-code-path "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent" \
  --mode SNAPSHOT
```

---

## 参考

- App URL: https://idom-car-ai-1444828305810485.aws.databricksapps.com/
- ワークスペース: e2-demo-field-eng (1444828305810485)
- SQL Warehouse: `my_warehouse` (ID: `03560442e95cb440`)

*最終更新: 2026-03-28*
