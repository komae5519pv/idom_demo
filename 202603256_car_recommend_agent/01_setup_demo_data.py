# Databricks notebook source
# MAGIC %md
# MAGIC # 01_setup_demo_data
# MAGIC
# MAGIC デモ用のサンプルデータを生成します。
# MAGIC
# MAGIC - **顧客商談データ**: 3パターンの顧客プロファイル
# MAGIC - **在庫車両データ**: 9台の車両情報
# MAGIC
# MAGIC > サーバレスコンピュートまたはSQLウェアハウスで実行してください

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定読み込み

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 顧客商談データ作成
# MAGIC
# MAGIC 3パターンの顧客を用意:
# MAGIC 1. **ファミリー層**: ミニバン希望、予算200-300万
# MAGIC 2. **単身者/カップル**: コンパクト/SUV希望、予算150-250万
# MAGIC 3. **高級志向**: プレミアムSUV希望、予算400万以上

# COMMAND ----------

# DBTITLE 1,顧客商談データ
from pyspark.sql.types import StructType, StructField, StringType, DateType
from datetime import date

# 商談録音テキストサンプル
transcripts = [
    # 顧客1: ファミリー層（ミニバン希望）
    {
        "interaction_id": "INT001",
        "customer_id": "C001",
        "customer_name": "田中 太郎",
        "interaction_type": "recording",
        "transcript": """営業：本日はご来店ありがとうございます。どのようなお車をお探しですか？

顧客：実は今乗っているコンパクトカーが手狭になってきて。子供が2人いるんですが、上の子が中学生になって部活の送り迎えとか荷物も増えてきて。

営業：なるほど、お子様の成長に合わせてですね。ご家族4人でお乗りになることが多いですか？

顧客：そうですね、週末は家族で出かけることが多いです。あと、妻も運転するので、あまり大きすぎると怖いって言っていて。

営業：奥様も運転されるんですね。ご予算はどのくらいをお考えですか？

顧客：できれば200万円台で収めたいんですが、いい車があれば300万円くらいまでは考えてもいいかなと。

営業：承知しました。安全装備とかは気にされますか？

顧客：はい、子供を乗せるので、自動ブレーキとかは絶対欲しいです。あと燃費も気になりますね。ガソリン代が馬鹿にならないので。""",
        "interaction_date": date(2026, 3, 20),
        "store_id": "STORE001"
    },
    # 顧客2: 単身者/カップル（コンパクトSUV希望）
    {
        "interaction_id": "INT002",
        "customer_id": "C002",
        "customer_name": "鈴木 花子",
        "interaction_type": "line",
        "transcript": """お問い合わせありがとうございます。

私は28歳の会社員で、彼氏と2人暮らしです。今は電車通勤なんですが、週末のアウトドアや旅行用に車が欲しくて探しています。

キャンプとかスノボに行くことが多いので、荷物が積めるSUVタイプがいいなと思っています。でも都内に住んでいるので、あまり大きいと駐車場が困るかなと。

予算は150万から200万くらいで考えています。250万くらいまでならローンも検討します。

デザインがおしゃれな車がいいです。あと、運転に自信がないので、駐車をサポートしてくれる機能があると嬉しいです。""",
        "interaction_date": date(2026, 3, 21),
        "store_id": "STORE002"
    },
    # 顧客3: 高級志向（プレミアムSUV/ミニバン希望）
    {
        "interaction_id": "INT003",
        "customer_id": "C003",
        "customer_name": "山田 健一",
        "interaction_type": "recording",
        "transcript": """営業：山田様、本日はご来店いただきありがとうございます。

顧客：ええ、今乗っているベンツのSUVがそろそろ5年になるので、乗り換えを検討しています。

営業：なるほど、現在はメルセデスにお乗りなんですね。今回もSUVをお探しですか？

顧客：そうですね、SUVか高級ミニバンを考えています。取引先を乗せることもあるので、見栄えのいい車がいいですね。

営業：ご予算はいかがでしょうか？

顧客：500万から800万くらいで考えています。いい車があれば多少オーバーしても構いません。

営業：かしこまりました。装備面でご希望はありますか？

顧客：最新の安全装備は当然として、革シートやサンルーフは欲しいですね。あと、ゴルフに行くのでトランクは広めがいい。ナビは大画面のものを。静粛性も重視します。長距離でも疲れない車がいいですね。""",
        "interaction_date": date(2026, 3, 22),
        "store_id": "STORE001"
    }
]

# DataFrameに変換
schema = StructType([
    StructField("interaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("customer_name", StringType(), False),
    StructField("interaction_type", StringType(), False),
    StructField("transcript", StringType(), False),
    StructField("interaction_date", DateType(), False),
    StructField("store_id", StringType(), False)
])

df_interactions = spark.createDataFrame(transcripts, schema)
display(df_interactions)

# COMMAND ----------

# DBTITLE 1,顧客商談テーブル保存
df_interactions.write.mode("overwrite").saveAsTable("customer_interactions")
print("customer_interactions テーブルを作成しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 在庫車両データ作成
# MAGIC
# MAGIC 9台の車両情報を登録（画像ファイルと対応）

# COMMAND ----------

# DBTITLE 1,在庫車両データ
from pyspark.sql.types import IntegerType, ArrayType

# 画像のベースパス
image_base_path = "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_recommend_agent/_images"

vehicles = [
    {
        "vehicle_id": "V001",
        "make": "ホンダ",
        "model": "N-BOX",
        "year": 2023,
        "price": 1480000,
        "mileage": 15000,
        "body_type": "軽自動車",
        "fuel_type": "ガソリン",
        "seating_capacity": 4,
        "features": ["自動ブレーキ", "スライドドア", "低燃費"],
        "image_path": f"{image_base_path}/nbox.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V002",
        "make": "ホンダ",
        "model": "フリード",
        "year": 2023,
        "price": 2280000,
        "mileage": 12000,
        "body_type": "コンパクトミニバン",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 6,
        "features": ["自動ブレーキ", "低燃費", "両側スライドドア", "Honda SENSING"],
        "image_path": f"{image_base_path}/freed.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V003",
        "make": "トヨタ",
        "model": "シエンタ",
        "year": 2024,
        "price": 2450000,
        "mileage": 8000,
        "body_type": "コンパクトミニバン",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 7,
        "features": ["自動ブレーキ", "低燃費", "両側スライドドア", "Toyota Safety Sense"],
        "image_path": f"{image_base_path}/sienta.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V004",
        "make": "トヨタ",
        "model": "ヴォクシー",
        "year": 2023,
        "price": 2980000,
        "mileage": 20000,
        "body_type": "ミニバン",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 7,
        "features": ["自動ブレーキ", "低燃費", "両側スライドドア", "Toyota Safety Sense", "広い室内"],
        "image_path": f"{image_base_path}/voxy.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V005",
        "make": "トヨタ",
        "model": "アルファード",
        "year": 2022,
        "price": 5200000,
        "mileage": 25000,
        "body_type": "高級ミニバン",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 7,
        "features": ["自動ブレーキ", "本革シート", "サンルーフ", "JBLサウンド", "Toyota Safety Sense", "静粛性"],
        "image_path": f"{image_base_path}/alphard.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V006",
        "make": "ホンダ",
        "model": "ヴェゼル",
        "year": 2024,
        "price": 2350000,
        "mileage": 5000,
        "body_type": "コンパクトSUV",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 5,
        "features": ["自動ブレーキ", "低燃費", "Honda SENSING", "パーキングサポート", "おしゃれデザイン"],
        "image_path": f"{image_base_path}/vezel.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V007",
        "make": "トヨタ",
        "model": "ハリアー",
        "year": 2023,
        "price": 3800000,
        "mileage": 18000,
        "body_type": "SUV",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 5,
        "features": ["自動ブレーキ", "本革シート", "Toyota Safety Sense", "パノラマルーフ", "JBLサウンド"],
        "image_path": f"{image_base_path}/harrier.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V008",
        "make": "レクサス",
        "model": "RX",
        "year": 2023,
        "price": 6800000,
        "mileage": 15000,
        "body_type": "プレミアムSUV",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 5,
        "features": ["自動ブレーキ", "本革シート", "サンルーフ", "Mark Levinsonサウンド", "Lexus Safety System+", "静粛性", "大画面ナビ"],
        "image_path": f"{image_base_path}/lexus_rx.jpg",
        "stock_status": "在庫あり"
    },
    {
        "vehicle_id": "V009",
        "make": "トヨタ",
        "model": "プリウス",
        "year": 2024,
        "price": 2950000,
        "mileage": 3000,
        "body_type": "セダン",
        "fuel_type": "ハイブリッド",
        "seating_capacity": 5,
        "features": ["自動ブレーキ", "低燃費", "Toyota Safety Sense", "先進デザイン"],
        "image_path": f"{image_base_path}/prius.jpg",
        "stock_status": "在庫あり"
    }
]

# features列をArrayTypeに変換するため、一度リストを文字列化してから処理
df_vehicles = spark.createDataFrame(vehicles)
display(df_vehicles)

# COMMAND ----------

# DBTITLE 1,在庫車両テーブル保存
df_vehicles.write.mode("overwrite").saveAsTable("vehicle_inventory")
print("vehicle_inventory テーブルを作成しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. データ確認

# COMMAND ----------

# DBTITLE 1,顧客商談データ確認
# MAGIC %sql
# MAGIC SELECT * FROM customer_interactions

# COMMAND ----------

# DBTITLE 1,在庫車両データ確認
# MAGIC %sql
# MAGIC SELECT vehicle_id, make, model, price, body_type, fuel_type, features
# MAGIC FROM vehicle_inventory
# MAGIC ORDER BY price

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ完了
# MAGIC
# MAGIC 以下のテーブルが作成されました：
# MAGIC - `customer_interactions`: 顧客商談データ（3件）
# MAGIC - `vehicle_inventory`: 在庫車両データ（9台）
# MAGIC
# MAGIC 次のステップ: `02_recommend_demo` を実行してください。
