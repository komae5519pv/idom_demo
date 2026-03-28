# IDOM Car AI - アプリ実装設計書

> **最終更新**: 2026-03-26

---

## 1. デモ概要

### 1.1 ユースケース
営業担当者が顧客対応時に、AIが商談内容から顧客ニーズを自動抽出し、最適な車両を提案するシステム。

### 1.2 処理フロー

```
入力: 顧客との商談録音テキスト / LINE問い合わせ
  ↓
AI Functions: 非構造化データからニーズを構造化抽出
  ↓
マッチング: 在庫車両とのスコアリング
  ↓
出力: おすすめ車両3台 + 提案理由 + トークスクリプト
```

### 1.3 Databricks機能の活用

| 機能 | 用途 |
|------|------|
| **Databricks Apps** | フルスタックWebアプリケーション |
| **AI Functions** | SQLでLLM呼び出し、非構造化→構造化変換 |
| **Unity Catalog** | データガバナンス・アクセス制御 |
| **Foundation Model API** | トークスクリプト生成 |
| **Delta Lake** | データレイク基盤 |

---

## 2. アプリ構成

### 2.1 ディレクトリ構造

```
20260406_car_ai_agent/
├── app.yaml              # Databricks Apps設定
├── requirements.txt      # Python依存関係
├── _images/              # 車両画像（10車種）
│   ├── alphard.jpg
│   ├── freed.jpg
│   ├── harrier.jpg
│   ├── lexus_rx.jpg
│   ├── nbox.jpg
│   ├── prius.jpg
│   ├── sienta.jpg
│   ├── vezel.jpg
│   ├── volvo_xc60.jpg
│   └── voxy.jpg
├── app/
│   ├── backend/          # FastAPI バックエンド
│   │   └── app/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── llm.py
│   │       ├── demo_data.py
│   │       ├── models.py
│   │       └── routers/
│   │           ├── customers.py
│   │           ├── recommendations.py
│   │           ├── chat.py
│   │           └── admin.py
│   └── dist/             # ビルド済みフロントエンド
│       ├── index.html
│       └── assets/
├── 00_config             # 設定ノートブック
└── 01_setup_demo_data    # デモデータセットアップ
```

### 2.2 技術スタック

#### Frontend
| カテゴリ | 技術 | バージョン |
|---------|------|-----------|
| Framework | React | 19.x |
| Language | TypeScript | 5.9.x |
| Styling | TailwindCSS | 4.x |
| Icons | React Icons | - |
| Build | Vite | 6.x |

#### Backend
| カテゴリ | 技術 |
|---------|------|
| Framework | FastAPI |
| Runtime | Python 3.11+ |
| DB Client | Databricks SQL Connector |
| LLM Client | OpenAI SDK (Foundation Model API) |

---

## 3. 画面構成

### 3.1 顧客一覧画面 (`/sales`)
- 顧客カードのリスト表示
- 検索機能
- 顧客クリックで詳細画面へ

### 3.2 顧客詳細画面 (`/sales/customers/:customerId`)

**セクション構成（上から順に流れる縦方向レイアウト）：**

```
┌─────────────────────────────────────┐
│  ← 戻る   山田太郎                    │
│          IT企業管理職 / 妻と子供2人   │
├─────────────────────────────────────┤
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🔵 顧客情報                       │ │ ← グラデーション: blue → indigo
│  │ 氏名、職業、家族構成、現在の車    │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🟠 印象的な発言                   │ │ ← グラデーション: amber → orange
│  │ 「子供の送り迎えに...」           │ │    ※ key_quotesから取得
│  │ 「燃費も気になります」            │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🎤 商談録音テキスト（全文） ▼     │ │ ← 折りたたみ式（デフォルト閉）
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🟣 AIインサイト                   │ │ ← グラデーション: purple → pink
│  │ ・主要ニーズ                      │ │
│  │ ・深層インサイト                  │ │
│  │ ・購買意欲                        │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🔷 基本条件                       │ │ ← グラデーション: cyan → blue
│  │ ご予算: ¥2,000,000 〜 ¥3,000,000 │ │
│  │ 重視: [安全装備] [燃費]           │ │
│  │ NG: [大きすぎる車]                │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 🟢 お客様におすすめの車両  [再生成]│ │ ← グラデーション: green → teal
│  │                                   │ │
│  │ ┌─────┬───────────────────────┐ │ │
│  │ │     │ #1 おすすめ           │ │ │
│  │ │画像 │ トヨタ シエンタ ¥2.45M│ │ │    ※ 横レイアウト（画像左）
│  │ │     │ なぜこの車が最適か... │ │ │
│  │ │     │ この車のある生活...   │ │ │
│  │ └─────┴───────────────────────┘ │ │
│  │ （#2, #3も同様）                  │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │ 📝 提案トークスクリプト  [コピー] │ │ ← グラデーション: emerald → green
│  │                                   │ │    ※ Markdownを整形表示
│  │ ## アイスブレイク               │ │
│  │ お子様の成長に合わせて...        │ │
│  └─────────────────────────────────┘ │
│                                       │
└─────────────────────────────────────┘
```

---

## 4. UI/UX要件

### 4.1 全体デザイン
- **縦方向に流れるレイアウト**（横幅ギチギチにしない）
- `max-width: 4xl` (896px) でセンタリング
- 各セクションは `rounded-2xl` で角丸
- グラデーションヘッダーで視覚的に区切る
- 適切な余白 (`space-y-6`) でセクション間を区切る
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
- **画像**: `object-cover object-center` で見切れ防止

---

## 5. API エンドポイント

### Customer API
```
GET  /api/customers                    # 顧客一覧
GET  /api/customers/:id                # 顧客詳細
GET  /api/customers/:id/insights       # AIインサイト
GET  /api/customers/:id/interaction    # 商談データ（transcript, key_quotes）
```

### Recommendation API
```
GET  /api/customers/:id/recommendations    # レコメンド取得
POST /api/recommendations/regenerate       # レコメンド再生成
```

### Chat API
```
POST /api/chat                         # チャット送信
POST /api/chat/stream                  # ストリーミングチャット
```

### Admin API
```
GET  /api/admin/stats                  # 統計情報
GET  /api/admin/traces                 # トレース一覧
```

### その他
```
GET  /api/health                       # ヘルスチェック
GET  /api/images/:filename             # 車両画像配信
```

---

## 6. データモデル

### 6.1 顧客データ
```typescript
interface Customer {
  customer_id: string
  name: string
  age: number
  occupation: string
  family_structure: string
  budget_min: number
  budget_max: number
  current_car?: string
}
```

### 6.2 商談データ
```typescript
interface CustomerInteraction {
  transcript: string           // 商談録音テキスト全文
  interaction_date?: string
  interaction_type?: string
  key_quotes?: string[]        // 印象的な発言
}
```

### 6.3 AIインサイト
```typescript
interface CustomerInsight {
  needs: string[]              // 主要ニーズ
  priorities: string[]         // 重視ポイント
  avoid: string[]              // 避けたい要素
  purchase_intent: string      // 購買意欲
  key_insight?: string         // 深層インサイト
}
```

### 6.4 車両レコメンド
```typescript
interface VehicleRecommendation {
  vehicle: Vehicle
  match_score: number          // マッチ度（0-100）
  reason: string               // なぜこの車が最適か
  headline?: string            // キャッチコピー
  life_scene?: string          // この車のある生活シーン
}
```

---

## 7. デモデータ

### 7.1 顧客データ（5名）
| ID | 名前 | 年齢 | 職業 | 家族構成 | 予算 |
|----|------|------|------|---------|------|
| C001 | 山田太郎 | 42 | IT企業管理職 | 妻と子供2人 | 200-300万 |
| C002 | 鈴木花子 | 35 | 医療従事者 | 夫と子供1人 | 180-280万 |
| C003 | 田中一郎 | 55 | 自営業 | 夫婦2人 | 400-600万 |
| C004 | 佐藤美咲 | 28 | 会社員 | 独身 | 150-250万 |
| C005 | 伊藤健一 | 48 | 建設業 | 妻と子供3人 | 300-450万 |

### 7.2 車両データ（10台）
| 車種 | タイプ | 価格帯 | 特徴 |
|------|--------|--------|------|
| N-BOX | 軽 | 100-150万 | コンパクト、低燃費 |
| フリード | ミニバン（小） | 180-250万 | コンパクトミニバン |
| シエンタ | ミニバン（小） | 180-250万 | ハイブリッド |
| ヴォクシー | ミニバン（中） | 250-350万 | ファミリー向け |
| アルファード | ミニバン（大） | 400-600万 | 高級ミニバン |
| ヴェゼル | SUV（小） | 200-300万 | コンパクトSUV |
| ハリアー | SUV（中） | 300-450万 | 高級SUV |
| レクサスRX | SUV（大） | 500-800万 | プレミアムSUV |
| プリウス | セダン | 250-350万 | ハイブリッド |
| ボルボXC60 | SUV | 500-700万 | 北欧デザイン |

---

## 8. デプロイ手順

### 8.1 フロントエンドビルド
```bash
cd /Users/konomi.omae/code/idom-car-ai/app/frontend
npm run build
```

### 8.2 ワークスペースへアップロード
```bash
# Python スクリプトでアップロード（upload_frontend.py）
# dist/ → app/dist/
# backend/*.py → app/backend/app/
```

### 8.3 デプロイ
```bash
databricks apps deploy idom-car-ai \
  --source-code-path /Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent \
  --profile=e2-demo-west
```

---

## 9. 環境情報

| 項目 | 値 |
|------|-----|
| Workspace | `e2-demo-field-eng.cloud.databricks.com` |
| App URL | `https://idom-car-ai-1444828305810485.aws.databricksapps.com/` |
| Source Path | `/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_ai_agent` |
| Profile | `e2-demo-west` |

---

## 10. 参考

### プロトタイプノートブック
`/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_recommend_agent/02_recommend_demo`

このノートブックのUI要素を参考に、良い要素を取り入れてアプリをパワーアップする。

### ローカル開発環境
`/Users/konomi.omae/code/idom-car-ai/`
