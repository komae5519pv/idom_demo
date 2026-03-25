# IDOM 車両提案AI デモ - 実装設計書

> **最終更新**: 2026-03-25

---

## 1. デモ概要

### 1.1 ユースケース
営業担当者が顧客対応時に、AIが商談内容から顧客ニーズを自動抽出し、最適な車両を提案するデモ。

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
| **AI Functions** | SQLでLLM呼び出し、非構造化→構造化変換（ai_extract, ai_classify） |
| **Unity Catalog** | データガバナンス・アクセス制御 |
| **Foundation Model API** | トークスクリプト生成 |
| **Delta Lake** | データレイク基盤 |

---

## 2. 技術仕様

### 2.1 環境

| 項目 | 値 |
|------|-----|
| Workspace | `e2-demo-field-eng.cloud.databricks.com` |
| Catalog | `{catalog_name}` ※00_configで定義 |
| Schema | `{schema_name}` ※00_configで定義 |
| 作業ディレクトリ | `/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_recommend_agent` |

### 2.2 00_config 設定値

```python
# 00_config で定義（変更可能）
catalog_name = "komae_demo_v4"      # ← 必要に応じて変更
schema_name = "car_recommend_agent" # ← 必要に応じて変更

# スキーマ作成・USE設定
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")
spark.sql(f"USE CATALOG {catalog_name}")
spark.sql(f"USE SCHEMA {schema_name}")
```

### 2.3 ディレクトリ構成

```
20260406_car_recommend_agent/
├── 00_config              # 設定（既存）
├── 01_setup_demo_data     # サンプルデータ生成
├── 02_recommend_demo      # レコメンドデモ本体
├── _images/               # 車両画像（アップロード済み）
│   ├── alphard.jpg
│   ├── freed.jpg
│   ├── harrier.jpg
│   ├── lexus_rx.jpg
│   ├── nbox.jpg
│   ├── prius.jpg
│   ├── sienta.jpg
│   ├── vezel.jpg
│   └── voxy.jpg
└── README.md              # この文書
```

### 2.4 実装アプローチ

**Phase 1: Notebook + displayHTML（今回）**
- Notebookで完結
- `displayHTML()`でリッチな結果表示
- 車両画像付きカード形式

**Phase 2: Databricks Apps（将来）**
- React/Gradioで本格UI

---

## 3. データモデル

### 3.1 顧客商談テーブル

```sql
-- {catalog_name}.{schema_name}.customer_interactions
CREATE TABLE IF NOT EXISTS customer_interactions (
  interaction_id STRING,
  customer_id STRING,
  customer_name STRING,
  interaction_type STRING,  -- 'recording', 'line', 'call_center'
  transcript TEXT,          -- 商談録音テキスト
  interaction_date DATE,
  store_id STRING
);
```

### 3.2 在庫車両テーブル

```sql
-- {catalog_name}.{schema_name}.vehicle_inventory
CREATE TABLE IF NOT EXISTS vehicle_inventory (
  vehicle_id STRING,
  make STRING,              -- メーカー
  model STRING,             -- 車種名
  year INT,                 -- 年式
  price INT,                -- 価格
  mileage INT,              -- 走行距離
  body_type STRING,         -- ボディタイプ（ミニバン、SUV等）
  fuel_type STRING,         -- 燃料（ガソリン、ハイブリッド等）
  seating_capacity INT,     -- 乗車定員
  features ARRAY<STRING>,   -- 特徴（安全装備等）
  image_path STRING,        -- 画像パス
  stock_status STRING       -- 在庫状況
);
```

### 3.3 AI Functions出力構造

```sql
-- ai_extract()の出力
STRUCT<
  desired_body_type: STRING,      -- 希望ボディタイプ
  budget_min: INT,                -- 予算下限
  budget_max: INT,                -- 予算上限
  family_size: INT,               -- 家族人数
  primary_use: STRING,            -- 主な用途
  must_have_features: ARRAY<STRING>, -- 必須機能
  concerns: ARRAY<STRING>,        -- 懸念点
  sentiment: STRING               -- 購買意欲（高/中/低）
>
```

---

## 4. サンプルデータ

### 4.1 商談録音サンプル

```
営業：本日はご来店ありがとうございます。どのようなお車をお探しですか？

顧客：実は今乗っているコンパクトカーが手狭になってきて。子供が2人いるんですが、
上の子が中学生になって部活の送り迎えとか荷物も増えてきて。

営業：なるほど、お子様の成長に合わせてですね。ご家族4人でお乗りになることが多いですか？

顧客：そうですね、週末は家族で出かけることが多いです。
あと、妻も運転するので、あまり大きすぎると怖いって言っていて。

営業：奥様も運転されるんですね。ご予算はどのくらいをお考えですか？

顧客：できれば200万円台で収めたいんですが、いい車があれば300万円くらいまでは考えてもいいかなと。

営業：承知しました。安全装備とかは気にされますか？

顧客：はい、子供を乗せるので、自動ブレーキとかは絶対欲しいです。あと燃費も気になりますね。
```

### 4.2 期待されるAI抽出結果

```json
{
  "desired_body_type": "ミニバン",
  "budget_min": 2000000,
  "budget_max": 3000000,
  "family_size": 4,
  "primary_use": "ファミリー・レジャー",
  "must_have_features": ["自動ブレーキ", "低燃費"],
  "concerns": ["サイズが大きすぎると運転しにくい"],
  "sentiment": "高"
}
```

### 4.3 在庫車両（9台）

| 車種 | タイプ | 価格帯 | 特徴 |
|------|--------|--------|------|
| N-BOX | 軽 | 100-150万 | コンパクト、低燃費 |
| フリード | ミニバン（小） | 180-250万 | コンパクトミニバン、運転しやすい |
| シエンタ | ミニバン（小） | 180-250万 | コンパクトミニバン、ハイブリッド |
| ヴォクシー | ミニバン（中） | 250-350万 | ファミリー向け、広い室内 |
| アルファード | ミニバン（大） | 400-600万 | 高級ミニバン |
| ヴェゼル | SUV（小） | 200-300万 | コンパクトSUV |
| ハリアー | SUV（中） | 300-450万 | 高級SUV |
| レクサスRX | SUV（大） | 500-800万 | プレミアムSUV |
| プリウス | セダン | 250-350万 | ハイブリッド、低燃費 |

---

## 5. 実装詳細

### 5.1 01_setup_demo_data

```python
# Step 1: 設定読み込み
%run ./00_config

# Step 2: 顧客商談データ作成（3-5件）
# - ファミリー層（ミニバン希望）
# - 単身者（コンパクト希望）
# - 高級志向（SUV/高級車希望）

# Step 3: 在庫車両データ作成（9台）

# Step 4: テーブル登録
```

### 5.2 02_recommend_demo

```python
# Step 1: 顧客選択
customer_id = "C001"

# Step 2: 商談テキスト取得
transcript = spark.sql("""
  SELECT transcript FROM customer_interactions
  WHERE customer_id = '{}'
""".format(customer_id)).collect()[0][0]

# Step 3: AI Functionsでニーズ抽出
needs = spark.sql("""
  SELECT ai_extract(
    '{}',
    ARRAY('desired_body_type', 'budget_min', 'budget_max',
          'family_size', 'must_have_features', 'concerns')
  ) as needs
""".format(transcript)).collect()[0][0]

# Step 4: 在庫マッチング
# - 予算フィルタ
# - ボディタイプマッチ
# - 必須機能チェック

# Step 5: レコメンド理由生成（Foundation Model API）

# Step 6: トークスクリプト生成

# Step 7: displayHTML()で結果表示
```

---

## 6. UI出力イメージ

```
┌─────────────────────────────────────────────────────────────────┐
│  🚗 車両提案AI                                                    │
├─────────────────────────────────────────────────────────────────┤
│  【抽出されたニーズ】                                              │
│  ・希望タイプ: ミニバン                                           │
│  ・予算: 200-300万円                                              │
│  ・家族構成: 4人                                                  │
│  ・必須機能: 自動ブレーキ、低燃費                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                        │
│  │  [画像]   │  │  [画像]   │  │  [画像]   │                        │
│  │  フリード │  │ シエンタ │  │ ヴォクシー │                       │
│  │  228万円  │  │  245万円  │  │  298万円  │                        │
│  │マッチ度95%│  │マッチ度92%│  │マッチ度85%│                        │
│  └──────────┘  └──────────┘  └──────────┘                        │
│                                                                   │
│  【おすすめ理由】                                                   │
│  コンパクトミニバンなので運転しやすく、安全装備も充実...            │
│                                                                   │
│  【提案トーク】                                                    │
│  「フリードはコンパクトながら3列シートで...」                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. フォールバック戦略

Web閲覧履歴がない顧客の場合:
1. **類似顧客マッチング**: 同属性の過去成約データから傾向を推定
2. **商談テキスト重視**: 会話から直接ニーズを抽出

---

## 8. チェックリスト

### 実装前
- [x] 要件定義完了
- [x] 車両画像アップロード
- [ ] 実装Goサイン

### 実装
- [ ] 01_setup_demo_data 作成
- [ ] 02_recommend_demo 作成
- [ ] AI Functions動作確認
- [ ] displayHTML出力確認

---

## 9. 関連ファイル

- デモコンセプトHTML: `~/Desktop/client/IDOM/デモ/idom_vehicle_ai_demo_concept.html`
- アーキテクチャHTML: `~/Desktop/client/IDOM/デモ/idom_architecture.html`
