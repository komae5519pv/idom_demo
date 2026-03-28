# IDOM Car AI - アプリ実装設計書

> **最終更新**: 2026-03-28

---

## 1. デモ概要

### 1.1 ユースケース
営業担当者が顧客対応時に、AIが商談内容から顧客ニーズを自動抽出し、最適な車両を提案するシステム。

### 1.2 処理フロー

```
入力: 顧客との商談録音テキスト（Unity Catalogに格納済み）
  ↓
RAG: UCテーブルから顧客プロフィール・商談録音・インサイトを取得
  ↓
Foundation Model API: ニーズ抽出 → 在庫とマッチング → 推薦理由生成
  ↓
出力: おすすめ車両3台 + 提案理由 + トークスクリプト + AIチャット
```

### 1.3 Databricks機能の活用

| 機能 | 用途 |
|------|------|
| **Databricks Apps** | フルスタックWebアプリケーション |
| **Unity Catalog** | 顧客・車両・商談データのガバナンス |
| **Foundation Model API** | 推薦理由・トークスクリプト・チャット生成 |
| **Delta Lake** | Bronze（録音テキスト）→Silver（インサイト）→Gold（推薦） |
| **MLflow Tracing** | LLM呼び出しのトレーシング・品質評価 |

---

## 2. アプリ構成

### 2.1 ディレクトリ構造

```
20260406_car_ai_agent/
├── app.yaml              # Databricks Apps設定
├── requirements.txt      # Python依存関係
├── _images/              # 車両画像（10車種）
├── app/
│   ├── backend/          # FastAPI バックエンド
│   │   └── app/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── database.py      # Databricks SDK Statement Execution API
│   │       ├── llm.py           # Foundation Model API + MLflow trace
│   │       ├── demo_data.py     # フォールバック用デモデータ
│   │       ├── models.py
│   │       └── routers/
│   │           ├── customers.py
│   │           ├── recommendations.py
│   │           ├── chat.py      # RAG実装（UCから顧客コンテキスト取得）
│   │           └── admin.py
│   └── dist/             # ビルド済みフロントエンド（npm run build後にコピー）
├── 00_config             # UCセットアップノートブック
└── 01_setup_demo_data    # デモデータ投入ノートブック
```

### 2.2 技術スタック

| レイヤー | カテゴリ | 技術 | バージョン |
|---------|---------|------|-----------|
| Frontend | Framework | React | 19.x |
| Frontend | Language | TypeScript | 5.9.x |
| Frontend | Styling | TailwindCSS | 4.x |
| Frontend | Icons | React Icons | - |
| Frontend | Build | Vite | 6.x |
| Backend | Framework | FastAPI | - |
| Backend | Runtime | Python | 3.11+ |
| Backend | DB Client | Databricks SDK (Statement Execution API) | - |
| Backend | LLM Client | OpenAI SDK → Foundation Model API | - |
| Backend | Tracing | MLflow (`@mlflow.trace`) | - |

---

## 3. 画面構成

### 3.1 顧客一覧画面 (`/`)
- 顧客カードのリスト表示
- 検索機能
- 顧客クリックで詳細画面へ

### 3.2 顧客詳細画面 (`/customers/:customerId`)

**セクション構成（縦方向レイアウト）：**

```
┌─────────────────────────────────────┐
│  ← 戻る   山田 優子                  │
│          パート勤務（スーパー）       │
├─────────────────────────────────────┤
│  🔵 顧客情報（氏名、職業、家族構成、現在の車）  │
│  🟠 商談録音テキスト ▼（折りたたみ）           │
│  🟣 AIインサイト（深層ニーズ・購買意欲）        │
│  🔷 基本条件（予算・重視ポイント）              │
│  🟢 お客様におすすめの車両 [再生成]            │
│     #1 トヨタ シエンタ（マッチ度95%）          │
│     #2 ホンダ フリード（マッチ度88%）           │
│     #3 ...                                    │
│  📝 提案トークスクリプト [コピー]              │
│  💬 AIチャット（RAG付き）                      │
└─────────────────────────────────────┘
```

---

## 4. UI/UX要件

### 4.1 全体デザイン
- 縦方向に流れるレイアウト（`max-width: 4xl` でセンタリング）
- 各セクションは `rounded-2xl` で角丸
- グラデーションヘッダーで視覚的に区切る
- 背景色: `bg-gray-50`

### 4.2 カラースキーム

| セクション | グラデーション |
|-----------|---------------|
| 顧客情報 | blue-600 → indigo-600 |
| 印象的な発言 | amber-500 → orange-500 |
| AIインサイト | purple-600 → pink-600 |
| 基本条件 | cyan-600 → blue-600 |
| おすすめ車両 | green-600 → teal-600 |
| トークスクリプト | emerald-600 → green-600 |

### 4.3 重要な表示ルール
- **トークスクリプト**: Markdownを整形してHTML表示（#記号をそのまま表示しない）
- **商談録音テキスト**: 折りたたみ式（デフォルト閉じ、クリックで展開）
- **車両カード**: 横レイアウト（画像左、コンテンツ右）

---

## 5. API エンドポイント

### Customer API
```
GET  /api/customers                        # 顧客一覧
GET  /api/customers/:id                    # 顧客詳細
GET  /api/customers/:id/insights           # AIインサイト
GET  /api/customers/:id/interaction        # 商談データ（transcript）
```

### Recommendation API
```
GET  /api/customers/:id/recommendations    # レコメンド取得（LLM生成）
POST /api/customers/:id/recommendations/regenerate  # 再生成
GET  /api/vehicles                         # 車両一覧
```

### Chat API
```
POST /api/chat                             # チャット送信（RAG付き）
POST /api/chat/stream                      # ストリーミングチャット
GET  /api/chat/history/:session_id         # 履歴取得
DELETE /api/chat/history/:session_id       # 履歴クリア
```

### Admin API
```
GET  /api/admin/stats                      # 統計情報
GET  /api/admin/traces                     # MLflowトレース一覧
GET  /api/admin/evaluations                # LLM評価一覧
```

### その他
```
GET  /api/health                           # ヘルスチェック（database/llm接続状態）
GET  /api/images/:filename                 # 車両画像配信
```

---

## 6. データモデル（Pythonモデル）

### 6.1 顧客データ
```python
class Customer(BaseModel):
    customer_id: str
    name: str
    age: int
    gender: Optional[str]
    occupation: Optional[str]
    address: Optional[str]
    family_structure: Optional[str]
    current_vehicle: Optional[str]
    budget_min: Optional[int]
    budget_max: Optional[int]
    preferences: Optional[str]
    background: Optional[str]
```

### 6.2 車両レコメンド
```python
class VehicleRecommendation(BaseModel):
    vehicle: Vehicle
    match_score: int           # 0-100
    reason: str                # 推薦理由（顧客の発言を引用）
    headline: Optional[str]
```

---

## 7. Unity Catalogデータ（実データ）

### 7.1 顧客データ（4名）

| ID | 名前 | 年齢 | 職業 | 家族構成 | 予算 |
|----|------|------|------|---------|------|
| C001 | 山田 優子 | 38 | パート勤務（スーパー） | 夫・長女（小4）・長男（小1）・義母（72歳） | 180〜280万 |
| C002 | 佐藤 健一 | 52 | 中堅メーカー 営業部長 | 妻・長女（独立）・長男（大4） | 300〜450万 |
| C003 | 田中 翔太 | 29 | IT企業 システムエンジニア | 独身・彼女あり | 150〜230万 |
| C004 | 渡辺 雅子 | 45 | 外資系コンサル シニアマネージャー | 夫（医師）・長女（中2）・長男（小5） | 400〜600万 |

### 7.2 車両データ（10台）

| 車種 | メーカー | タイプ | 価格 | 特徴 |
|------|---------|--------|------|------|
| シエンタ | トヨタ | ミニバン | 228万 | 低床・両側電動スライドドア・Toyota Safety Sense |
| フリード | ホンダ | ミニバン | 205万 | Honda SENSING・コンパクト |
| ヴェゼル | ホンダ | SUV | 265万 | スタイリッシュ・e:HEV |
| ハリアー | トヨタ | SUV | 385万 | プレミアム・JBL・本革シート |
| プリウス | トヨタ | セダン | 329万 | 新デザイン・パノラマルーフ |
| レクサス NX | レクサス | SUV | 580万 | マークレビンソン・デジタルアウターミラー |
| ボルボ XC40 | ボルボ | SUV | 520万 | 安全性最高水準・Harman Kardon |
| アルファード | トヨタ | ミニバン | 720万 | 最上級・本革・JBL |
| フォレスター | スバル | SUV | 315万 | EyeSight・AWD・大型ガラスルーフ |
| BMW 3シリーズ | BMW | セダン | 498万 | 本革・ドライビングマシン |

---

## 8. RAG実装（chat.py）

チャットの新セッション開始時に UCテーブルから顧客コンテキストを取得してシステムプロンプトに注入：

```
customers テーブル      → 顧客プロフィール・背景・予算
customer_interactions  → 最新商談録音テキスト（直近1件）
customer_insights      → AI分析インサイト（存在する場合）
```

→ LLM が「山田様のお義母様（72歳）が乗り降りしやすい車は...」など個別化された回答を生成

---

## 9. デプロイ手順

### フロントエンドビルド & デプロイ
```bash
cd app/frontend
npm run build

# dist をコピー（FastAPIはapp/dist/をserveする）
rm -rf ../dist && cp -r dist ../dist

# Databricksワークスペースに同期してデプロイ
databricks apps deploy idom-car-ai \
  --source-code-path "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent" \
  --mode SNAPSHOT
```

### バックエンドのみ変更した場合
```bash
databricks workspace import /path/in/workspace \
  --file /local/file.py --format AUTO --overwrite

databricks apps deploy idom-car-ai \
  --source-code-path "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent" \
  --mode SNAPSHOT
```

---

## 10. 環境情報

| 項目 | 値 |
|------|-----|
| App URL | https://idom-car-ai-1444828305810485.aws.databricksapps.com/ |
| Workspace | e2-demo-field-eng.cloud.databricks.com (ID: 1444828305810485) |
| Source Path | `/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent` |
| SQL Warehouse | `my_warehouse` (ID: `03560442e95cb440`, Small) |
| Catalog | `komae_demo_v4` |
| Schema | `idom_car_ai` |
| LLM Model | `databricks-claude-sonnet-4` |
