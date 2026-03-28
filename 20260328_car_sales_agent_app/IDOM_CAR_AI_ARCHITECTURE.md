# IDOM Car AI - アーキテクチャ仕様書

## 概要

IDOM Car AI は、中古車販売店向けの AI アシスタント Databricks App です。
顧客の商談録音から嗜好を分析し、最適な車両をレコメンドします。

---

## デモモード vs 本番モード

### アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                      アプリ起動時                            │
├─────────────────────────────────────────────────────────────┤
│  DATABRICKS_WAREHOUSE_ID が設定されている？                  │
│                                                             │
│     YES → Unity Catalog に接続（本番モード）                 │
│     NO  → デモモードで起動（ハードコードされたデータを使用）  │
└─────────────────────────────────────────────────────────────┘
```

### 現在の状態（2026年3月時点）

**デモモードで動作中**
- Unity Catalog テーブルは作成されていない
- `app/backend/app/demo_data.py` のハードコードデータを使用
- LLM呼び出しもデモレスポンスを返却

---

## デモモードの仕組み

### データソース

| データ種別 | デモモード | 本番モード |
|-----------|-----------|-----------|
| 顧客データ | `DEMO_CUSTOMERS` | `komae_demo_v4.idom_car_ai.customers` |
| 車両在庫 | `DEMO_VEHICLES` | `komae_demo_v4.idom_car_ai.vehicle_inventory` |
| 商談録音 | `DEMO_INTERACTIONS` | `komae_demo_v4.idom_car_ai.customer_interactions` |
| 顧客インサイト | `DEMO_INSIGHTS` | `komae_demo_v4.idom_car_ai.customer_insights` |
| レコメンド | `DEMO_RECOMMENDATIONS` | LLM生成 + UC保存 |
| MLflowトレース | `DEMO_TRACES` | MLflow Tracking Server |
| 評価データ | `DEMO_EVALUATIONS` | MLflow Evaluation API |

### 関連ファイル

```
app/backend/app/
├── demo_data.py          # 全デモデータの定義
├── database.py           # UC接続 or デモモード判定
├── llm.py                # LLM接続 or デモレスポンス
├── config.py             # 設定（catalog, schema等）
└── routers/
    ├── customers.py      # USE_DEMO フラグで分岐
    ├── recommendations.py # USE_DEMO フラグで分岐
    └── admin.py          # DEMO_TRACES, DEMO_EVALUATIONS
```

### デモモード判定ロジック

```python
# app/backend/app/routers/customers.py
USE_DEMO = os.getenv("DEMO_MODE", "true").lower() == "true"

# app/backend/app/database.py
if not settings.databricks_warehouse_id:
    print("Databricks not configured - using demo mode")
    self._demo_mode = True
```

---

## Unity Catalog 設定

### テーブル構成

| テーブル名 | 説明 |
|-----------|------|
| `customers` | 顧客マスタ（名前、年齢、職業、予算等） |
| `vehicle_inventory` | 車両在庫（メーカー、車種、価格、走行距離等） |
| `customer_interactions` | 商談録音のトランスクリプト |
| `customer_insights` | LLMで抽出した顧客インサイト |
| `recommendations` | レコメンド結果の履歴 |

### 設定値

```yaml
# app.yaml
env:
  - name: 'CATALOG'
    value: 'komae_demo_v4'
  - name: 'SCHEMA_NAME'
    value: 'idom_car_ai'
  - name: 'DATABRICKS_WAREHOUSE_ID'
    value: ''  # 空 = デモモード
```

---

## 本番モードへの移行手順

### 1. Unity Catalog セットアップ

Databricks ワークスペースで以下のノートブックを順番に実行：

```
00_config.py        → カタログ、スキーマ、テーブル構造を作成
01_setup_demo_data.py → デモデータを投入
```

### 2. SQL Warehouse リソースの追加

Databricks Apps の UI で：
1. アプリの設定画面を開く
2. Resources タブで SQL Warehouse を追加
3. リソース名を `sql-warehouse` に設定

### 3. app.yaml の更新

```yaml
env:
  - name: 'DATABRICKS_WAREHOUSE_ID'
    valueFrom: 'sql-warehouse'  # リソースから取得

  - name: 'DEMO_MODE'
    value: 'false'
```

### 4. 再デプロイ

```bash
databricks apps deploy idom-car-ai --source-code-path /Workspace/Users/.../app
```

---

## LLMOps 機能（管理者画面）

### 概要

管理者画面では以下の LLMOps 機能を提供：

| 機能 | 説明 | デモモード |
|------|------|-----------|
| ダッシュボード | KPI概要（推論数、レイテンシ、エラー率） | `DEMO_TRACES` から集計 |
| MLflow Traces | LLM呼び出しのトレーシング | `DEMO_TRACES` を表示 |
| Gateway Metrics | Serving Endpoint メトリクス | ダミーデータ |
| Evaluations | LLM-as-Judge 評価 | `DEMO_EVALUATIONS` を表示 |
| Data Catalog | UC テーブル一覧 | 静的リスト |

### LLM-as-Judge とは

LLM の出力品質を別の LLM が評価する仕組み：

```
[ユーザー入力] → [対象LLM] → [出力] → [Judge LLM] → [スコア]
                                         ↓
                              Relevance, Faithfulness,
                              Helpfulness (1-5点)
```

**品質改善の方法：**
1. プロンプトエンジニアリング（Few-shot例、Chain-of-Thought）
2. RAG の改善（チャンク、埋め込みモデル、リランキング）
3. モデル選択・Temperature 調整
4. 低スコアケースの分析 → プロンプト改善 → 再評価

---

## フロントエンド構成

### 技術スタック

- React 19 + TypeScript 5.9
- TailwindCSS 4
- React Icons（アイコン）
- Vite（ビルド）

### ページ構成

```
/                    → 顧客一覧（営業担当向け）
/customers/:id       → 顧客詳細 + レコメンド + トークスクリプト
/admin               → 管理者ダッシュボード
/admin/traces        → MLflow Traces 一覧
/admin/gateway       → Gateway Metrics
/admin/evaluations   → LLM 評価一覧
/admin/catalog       → データカタログ
```

### トークスクリプト表示

顧客詳細ページのトークスクリプトは、セクション別にカード表示：

| セクション | 色 | アイコン |
|-----------|-----|---------|
| 導入 | 青 | 👋 |
| 共感ポイント | 紫 | 💜 |
| ご提案 | 緑 | 🚗 |
| クロージング | 黄 | 🎯 |

---

## デプロイ手順

### ビルド & デプロイ

```bash
# フロントエンドビルド
cd app/frontend
npm run build

# dist をコピー（重要！）
rm -rf ../dist
cp -r dist ../dist

# 同期 & デプロイ
cd ../..
databricks sync --watch . /Workspace/Users/.../app
databricks apps deploy idom-car-ai
```

**注意**: `app/dist/` と `app/frontend/dist/` は別物。FastAPI は `app/dist/` を serve するため、ビルド後に必ずコピーすること。

---

## 参考リンク

- アプリ URL: https://idom-car-ai-1444828305810485.aws.databricksapps.com/
- ワークスペース: e2-demo-field-eng

---

*最終更新: 2026-03-26*
