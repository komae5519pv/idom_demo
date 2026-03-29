# IDOM Car AI - 設計ドキュメント

> 営業担当者向け車両提案AIアプリケーション。顧客の深層ニーズを分析し、最適な車両をレコメンドする。

---

## 1. 概要

| 項目 | 値 |
|------|-----|
| アプリ名 | idom-car-ai |
| Workspace | e2-demo-field-eng.cloud.databricks.com |
| Catalog | komae_demo_v4 |
| Schema | idom_car_ai |
| App URL | https://idom-car-ai-1444828305810485.aws.databricksapps.com |
| App SP | `2cbe757a-6afe-4dc4-a375-151c10ab6735`（app-40zbx9 idom-car-ai） |

---

## 2. 技術スタック

| レイヤー | カテゴリ | 技術 | バージョン |
|---------|---------|------|-----------|
| Frontend | Framework | React | 19.x |
| Frontend | Language | TypeScript | 5.9.x |
| Frontend | Styling | TailwindCSS | 4.x |
| Frontend | Icons | React Icons (Fi, Hi2, Lu) | 5.x |
| Frontend | Build | Vite | 6.x |
| Frontend | State | Zustand | 5.x |
| Frontend | Router | react-router-dom | 7.x |
| Backend | Framework | FastAPI | >=0.115.0 |
| Backend | Runtime | Python | 3.11+ |
| Backend | DB Client | databricks-sql-connector | >=3.0.0 |
| Backend | DB SDK | Databricks SDK | >=0.30.0 |
| Backend | LLM Client | OpenAI SDK → Foundation Model API | >=1.52.0 |
| Backend | Tracing | MLflow (`@mlflow.trace`) | - |
| Infrastructure | Compute | Databricks Apps | - |
| Infrastructure | Data | Unity Catalog + Delta Lake | - |
| Infrastructure | AI/Agent | Multi-Agent Supervisor (MAS) endpoint | - |
| Infrastructure | Orchestration | DAB (Databricks Asset Bundles) | - |

---

## 3. ディレクトリ構成

```
idom-car-ai/
├── app.yml                         # Databricks Apps設定（起動コマンド・環境変数）
├── databricks.yml                  # DAB設定（bundle定義・sync先）
├── pyproject.toml                  # Pythonパッケージ設定（hatchling）
├── APP_REQUIREMENTS.md             # 本ドキュメント
├── 00_config.py                    # デモ環境設定スクリプト
├── 01_setup_demo_data.py           # デモデータ投入スクリプト
│
├── _images/                        # ローカル開発用フォールバック画像
│   └── volvo_xc60.jpg              # 唯一のローカル実画像
│
├── src/                            # Pythonソース（Databricks Appsにデプロイされる）
│   └── idom_car_ai/
│       ├── __dist__/               # フロントエンドビルド成果物（gitignore推奨）
│       └── backend/
│           ├── app.py              # FastAPIアプリケーション エントリーポイント
│           ├── config.py           # 設定（env vars・Databricks接続）
│           ├── database.py         # Databricks SQL接続管理
│           ├── demo_data.py        # デモモード用ダミーデータ
│           ├── llm.py              # LLM（Foundation Model API）クライアント
│           ├── models.py           # Pydanticモデル定義
│           └── routers/
│               ├── chat.py         # Ask AI チャットエンドポイント（MAS呼び出し）
│               ├── customers.py    # 顧客データAPI
│               ├── recommendations.py  # 車両レコメンドAPI
│               └── admin.py        # 管理者向けAPI（MLflow・Gateway監視）
│
├── app/
│   └── frontend/                   # Reactフロントエンド
│       ├── package.json
│       ├── vite.config.ts          # ビルド先: ../../src/idom_car_ai/__dist__
│       ├── tailwind.config.ts
│       └── src/
│           ├── api/index.ts        # バックエンドAPI呼び出し（SSE含む）
│           ├── store/index.ts      # Zustand グローバルステート
│           ├── types/              # TypeScript型定義
│           ├── pages/
│           │   ├── sales/          # 営業担当者向けUI
│           │   │   ├── CustomerList.tsx
│           │   │   └── CustomerDetail.tsx
│           │   └── admin/          # 管理者向けUI
│           └── components/
│               ├── chat/
│               │   └── ChatSidebar.tsx  # Ask AI サイドバー（幅調整・MD表示・履歴）
│               └── common/
│
└── .build/                         # デプロイ用ビルドディレクトリ（gitignore推奨）
    ├── app.yml
    ├── requirements.txt
    ├── idom_car_ai/                 # src/idom_car_ai/ のコピー + __dist__
    └── _images/                     # ローカル画像フォールバック
```

---

## 4. Unity Catalog 構成

### テーブル

| テーブル | 用途 |
|---------|------|
| `komae_demo_v4.idom_car_ai.customers` | 顧客マスタ |
| `komae_demo_v4.idom_car_ai.vehicle_inventory` | 在庫車両マスタ（`image_path`: ファイル名のみ） |
| `komae_demo_v4.idom_car_ai.customer_interactions` | 商談録音テキスト |
| `komae_demo_v4.idom_car_ai.customer_insights` | AI抽出インサイト（キャッシュ） |
| `komae_demo_v4.idom_car_ai.recommendations` | AI生成レコメンド（キャッシュ） |

### Volume

| Volume | 用途 | パス |
|--------|------|------|
| `komae_demo_v4.idom_car_ai.images` | 車両画像（JPEG） | `/Volumes/komae_demo_v4/idom_car_ai/images/` |
| `komae_demo_v4.idom_car_ai.knowledge` | RAG用ナレッジ文書 | `/Volumes/komae_demo_v4/idom_car_ai/knowledge/` |

**画像ファイル一覧:** `harrier.jpg`, `sienta.jpg`, `freed.jpg`, `voxy.jpg`, `alphard.jpg`, `vezel.jpg`, `prius.jpg`, `nbox.jpg`, `lexus_rx.jpg`

> `vehicle_inventory.image_path` はファイル名のみ（例: `"harrier.jpg"`）。アプリが `/api/images/{filename}` エンドポイント経由でVolumeからSDKストリーミング配信。

---

## 5. 権限設定（Databricks Apps SP）

Databricks Appsは専用のサービスプリンシパル（SP）で動作する。以下の権限を付与済み。

**SP情報:**
- Application ID: `2cbe757a-6afe-4dc4-a375-151c10ab6735`
- Display Name: `app-40zbx9 idom-car-ai`

**GRANTコマンド（新環境で再実行が必要）:**

```sql
-- アプリSPのApplication IDに置き換えること
GRANT USE CATALOG ON CATALOG <catalog_name> TO `<sp_application_id>`;
GRANT USE SCHEMA ON SCHEMA <catalog_name>.<schema_name> TO `<sp_application_id>`;
GRANT READ VOLUME ON VOLUME <catalog_name>.<schema_name>.images TO `<sp_application_id>`;

-- テーブルアクセスも必要な場合
GRANT SELECT ON SCHEMA <catalog_name>.<schema_name> TO `<sp_application_id>`;
```

> SPのApplication IDは `databricks apps get <app-name>` → `service_principal_id` → `databricks api get /api/2.0/preview/scim/v2/ServicePrincipals/<id>` → `applicationId` で確認。

### MAS（Model Serving）エンドポイントへの権限

Multi-Agent Supervisor エンドポイント（`mas-c850699f-endpoint`）にもアプリSPからのアクセス権限が必要。

**設定手順（UIから）:**
1. Databricks UI → **Serving** → 対象エンドポイント（`mas-c850699f-endpoint`）を開く
2. 右上の **Permission** ボタンをクリック
3. アプリSPのDisplay Name（`app-40zbx9 idom-car-ai`）を検索して追加
4. 権限: **Can Query**

> 新環境でエンドポイント名が変わる場合は `app.yml` の `AGENT_ENDPOINT_NAME` も合わせて更新すること。

---

## 6. 環境変数（app.yml）

| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| `CATALOG` | Unity Catalogカタログ名 | `komae_demo_v4` |
| `SCHEMA_NAME` | スキーマ名 | `idom_car_ai` |
| `LLM_MODEL` | Foundation Model API モデル名 | `databricks-claude-sonnet-4` |
| `AGENT_ENDPOINT_NAME` | Multi-Agent Supervisor エンドポイント名 | `mas-c850699f-endpoint` |
| `DATABRICKS_WAREHOUSE_ID` | SQL Warehouse ID（空=デモモード） | `""` |
| `PYTHONPATH` | Pythonモジュールパス | `"."` |
| `DEBUG` | デバッグフラグ | `"false"` |

> `DATABRICKS_WAREHOUSE_ID` が空の場合、`demo_data.py` のダミーデータを使用。実データを使う場合はWarehouse IDを設定。

---

## 7. デプロイ手順

### 前提条件

```bash
# Databricks CLI v0.263.0+
databricks --version

# Node.js 18+, npm
node --version

# Databricks profile設定済み
databricks auth status
```

### 手順

```bash
# 1. フロントエンドビルド
cd app/frontend
npm install
npm run build
# → src/idom_car_ai/__dist__/ に出力

# 2. フロントエンドをワークスペースにアップロード（必ずこのパスに）
databricks workspace import-dir src/idom_car_ai/__dist__ \
  /Workspace/Users/<your-email>/idom-car-ai/idom_car_ai/__dist__ --overwrite

# 3. Pythonソースをワークスペースにアップロード
databricks workspace import-dir src/idom_car_ai/backend \
  /Workspace/Users/<your-email>/idom-car-ai/idom_car_ai/backend --overwrite

# 4. app.yml・requirements.txtをアップロード
databricks workspace import /Workspace/Users/<your-email>/idom-car-ai/app.yml \
  --file app.yml --overwrite --format RAW
databricks workspace import /Workspace/Users/<your-email>/idom-car-ai/requirements.txt \
  --file requirements.txt --overwrite --format RAW

# 5. Databricks Appをデプロイ
databricks apps deploy idom-car-ai \
  --source-code-path /Workspace/Users/<your-email>/idom-car-ai
```

> ⚠️ **重要**: フロントエンドは必ず `src/idom_car_ai/__dist__` → `idom_car_ai/__dist__` に直接アップロードすること。`.build/` 経由で丸ごとアップロードすると古いJSで上書きされる。

### デプロイ後の確認

```bash
# アプリの状態確認
databricks apps get idom-car-ai

# ワークスペースのJSが最新か確認（ハッシュ値が新ビルドと一致すること）
databricks workspace list /Workspace/Users/<your-email>/idom-car-ai/idom_car_ai/__dist__/assets
```

---

## 8. MAS（Multi-Agent Supervisor）連携

- エンドポイント: `{DATABRICKS_HOST}/serving-endpoints/{AGENT_ENDPOINT_NAME}/invocations`
- リクエスト形式: `{"input": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]}`
- レスポンス: `output[]` の最後の非ルーティングメッセージが最終回答
- SSEでプログレス・コンテンツを分けてストリーミング配信

---

## 9. デモモードと本番モードの切り替え

| | デモモード | 本番モード |
|--|-----------|-----------|
| 切り替え | `DATABRICKS_WAREHOUSE_ID=''` | `DATABRICKS_WAREHOUSE_ID='<id>'` |
| データソース | `demo_data.py` | Unity Catalog テーブル |
| 顧客データ | ハードコード10名 | `customers` テーブル |
| レコメンド | `recommendations` テーブルなし→デモ固定 | AI生成キャッシュ読み込み |
| 画像 | Volume（権限設定済みなら同じ） | Volume |
