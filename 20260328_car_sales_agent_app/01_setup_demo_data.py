# Databricks notebook source
# MAGIC %md
# MAGIC # 01_setup_demo_data - デモデータ投入
# MAGIC
# MAGIC このノートブックでは、IDOM Car AIデモ用のサンプルデータを投入します。
# MAGIC
# MAGIC **前提条件**: `00_config` ノートブックを先に実行してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 設定読み込み

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# 00_configで定義された変数を補完
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME_NAME}"

print(f"Using: {FULL_SCHEMA}")
print(f"Volume path: {VOLUME_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 顧客データ投入

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from datetime import datetime

# 顧客データ
customers_data = [
    {
        "customer_id": "C001",
        "name": "山田 優子",
        "age": 38,
        "gender": "女性",
        "occupation": "パート勤務（スーパー）",
        "address": "千葉県船橋市",
        "family_structure": "夫（42歳・物流会社）、長女（小4）、長男（小1）、義母（72歳・同居）",
        "current_vehicle": "日産 セレナ（2016年式、12万km）",
        "budget_min": 1800000,
        "budget_max": 2800000,
        "preferences": "乗り降りしやすい、安全装備、運転しやすいサイズ",
        "background": """千葉県船橋市在住。夫は物流会社勤務で通勤に軽自動車を使用しているため、家族用の車は優子さんが主に運転。子供2人の習い事（ピアノ、水泳、塾）の送迎でほぼ毎日車を使用。義母が同居しており、週2回の病院送迎も担当。現在のセレナは8年目で走行12万km超え、最近エアコンの調子が悪く車検も近い。運転は自信がなく駐車で何度も切り返すことも。ママ友がアルファードに乗っていて羨ましいと思いつつ、予算的に現実的ではないと理解している。""",
        "created_at": datetime.now()
    },
    {
        "customer_id": "C002",
        "name": "佐藤 健一",
        "age": 52,
        "gender": "男性",
        "occupation": "中堅メーカー 営業部長",
        "address": "埼玉県さいたま市",
        "family_structure": "妻（50歳・専業主婦）、長女（社会人・独立）、長男（大学4年・就活中）",
        "current_vehicle": "トヨタ クラウン（2018年式、6万km）",
        "budget_min": 3000000,
        "budget_max": 4500000,
        "preferences": "ある程度の格、ゴルフバッグが積める、スタイリッシュ",
        "background": """埼玉県さいたま市在住の営業部長。来年定年が見えてきており、自費で維持しているクラウンの維持費を見直したいと考えている。妻は運転が苦手で最近は買い物の送迎も担当することが増えた。週末のゴルフが唯一の趣味で、バッグが積めることは必須条件。息子が就職したら車を貸してほしいと言っているが、愛着のある車を貸したくない本音がある。営業部長としてのプライドがあり軽自動車は絶対NGだが、本当はスポーツカーに乗りたい気持ちも。妻の「小さい車」希望との折り合いが課題。""",
        "created_at": datetime.now()
    },
    {
        "customer_id": "C003",
        "name": "田中 翔太",
        "age": 29,
        "gender": "男性",
        "occupation": "IT企業 システムエンジニア",
        "address": "東京都江東区",
        "family_structure": "独身、彼女あり（1年半）",
        "current_vehicle": "なし（初めての車購入）",
        "budget_min": 1500000,
        "budget_max": 2300000,
        "preferences": "彼女がSUV希望、かっこよければOK、実用的",
        "background": """東京都江東区の賃貸マンション住まい。IT企業でシステムエンジニアとして勤務。最近フルリモートから週2出社に変わり通勤に車があると便利だと感じ始めた。1年半付き合っている彼女が千葉の実家住まいで、会いに行くのにカーシェアを使っていたが週末は取れないことが多くストレス。車の知識はほぼゼロで何を基準に選べばいいかわからない状態。駐車場代が月3万円かかるため車両価格は抑えたい。彼女が「SUVがいい」と言っており、来年あたりプロポーズを考えている。結婚したら車のニーズも変わるかもと思いつつ、今は2人で使えれば十分。""",
        "created_at": datetime.now()
    },
    {
        "customer_id": "C004",
        "name": "渡辺 雅子",
        "age": 45,
        "gender": "女性",
        "occupation": "外資系コンサル会社 シニアマネージャー",
        "address": "神奈川県横浜市青葉区",
        "family_structure": "夫（47歳・医師）、長女（中2）、長男（小5）",
        "current_vehicle": "ボルボ XC60（2019年式、4万km）",
        "budget_min": 4000000,
        "budget_max": 6000000,
        "preferences": "安全性最優先、上質、積載量、ステータス",
        "background": """神奈川県横浜市青葉区在住。外資系コンサル会社のシニアマネージャーとして多忙な日々を送る。夫は医師でBMW X5を所有しているが、家族で出かける時は広さから雅子さんの車を使うことが多い。現在のボルボXC60はリース満了が近く、再リースか購入か新車かで迷っている。特に不満はないが周りでレクサスに乗っている人が多く気になっている。長女が中2でテニス部、遠征時は大荷物になるため積載量は必須。安全性は絶対条件で子供を乗せる車では妥協しない方針。夫は「好きなの選べば」と言うが家計管理は雅子さんが担当しており、コスパも密かに重視。""",
        "created_at": datetime.now()
    }
]

# DataFrameに変換して保存
customers_df = spark.createDataFrame(customers_data)
customers_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FULL_SCHEMA}.customers")

print(f"✓ 顧客データを {FULL_SCHEMA}.customers に投入しました（{len(customers_data)}件）")
display(spark.table(f"{FULL_SCHEMA}.customers").select("customer_id", "name", "age", "occupation"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 商談録音テキスト投入

# COMMAND ----------

from datetime import date
import uuid

# 商談録音データ（音声認識そのまま、話者識別なし）
interactions_data = [
    {
        "interaction_id": str(uuid.uuid4()),
        "customer_id": "C001",
        "interaction_date": date(2026, 3, 20),
        "interaction_type": "来店",
        "sales_rep": "鈴木 一郎",
        "transcript": """えっとですねあの今乗ってるのがセレナなんですけど もう8年くらいになるんですよねー 走行距離もけっこういっちゃってて12万キロ超えてるんです そうなんですよ最近ちょっとエアコンの調子も悪くて夏場とかやばいんですよね 子供乗せてるのにって思っちゃって あーそうなんです子供が2人いて 上が小4で下が小1なんですけど まあ元気で習い事とか送り迎えがすごい多くて 週に何回だろうえっとピアノと水泳と塾で まあほぼ毎日どっか行ってますね はい使うのはほぼ私ですね主人は別の車で通勤してるんで そうなんですあと義母も一緒に住んでて 足が悪いわけじゃないんですけどまあ歳なんで病院とか連れてったりとか 週2くらいで乗せることがあるんですよ だから乗り降りしやすい車がいいなって思ってて うーん予算はですねえっと諸費用込みで280万くらいまでで抑えたいなって思ってるんですけど どうですかね厳しいですか そうなんですよね広さも欲しいし安全なやつがいいし でも高いのは無理だしって はいアルファードとかママ友が乗ってて正直いいなーって思うんですけどさすがに予算が ははは夢ですよね いやでも広いのはいいですよね義母も乗りやすいだろうし シエンタとかフリードとかってどうなんですか 小さくないですか 実は見たことなくて そうなんですか3列あるんですね知らなかったです あと私運転そんな上手くないんで大きい車だとちょっと不安で 駐車とかいつも何回も切り返しちゃうんですよね はいそうなんです夫にも言われます下手だって まあ慣れなんでしょうけど でもやっぱり安全装備はちゃんとしてるのがいいです 子供乗せるんで何かあったら怖いじゃないですか 自動ブレーキとかついてるやつって今は普通なんですか へえ標準でついてるんですね それは安心ですね えっとあとは色とかは何でもいいんですけど 白とかシルバーとかが汚れ目立たなくていいかなって思ってます""",
        "duration_minutes": 12,
        "created_at": datetime.now()
    },
    {
        "interaction_id": str(uuid.uuid4()),
        "customer_id": "C002",
        "interaction_date": date(2026, 3, 21),
        "interaction_type": "来店",
        "sales_rep": "高橋 健太",
        "transcript": """あのね今クラウン乗ってるんだけど 2018年のやつ そろそろ乗り換えようかなと思って まあ不満があるわけじゃないんだけどね 維持費がね結構かかるでしょ ガソリン代とか税金とか まあ会社の車じゃないからさ全部自腹なわけ そう定年がね来年見えてきたから ちょっと考えないとなって 妻がねあんまり運転しないんだけど 最近買い物とか一緒に行くことが増えてさ 俺が運転手よ はは 娘はもう独立してて息子は大学4年なんだけど就活中でさ 車貸してくれって言うんだけどクラウンはちょっとな やっぱり自分のとして愛着あるからさ 週末ゴルフ行くのが唯一の趣味でね バッグ積めないと困るんだよ あと友達乗せることもあるから4人は乗れないと まあ予算はねどれくらいだろう400万くらいまでかな もうちょいいけるかもしれないけど まあ450万が上限だね 妻は小さい車がいいって言うんだけど 俺としてはさ営業部長やってきたプライドっていうの まあある程度の車には乗りたいわけ 軽とかは絶対無理ね 本当はさスポーツカーとか乗りたい気持ちもあるんだけど 現実的じゃないよな 歳も歳だし いやでもハリアーとかカッコいいよね 見た目がさ嫌いじゃない SUVって燃費どうなの 前はセダン一筋だったから全然わかんないんだよね あーそうなの ハイブリッドだと結構いいんだ へえ じゃあ維持費は今のクラウンよりは下がる感じ それはいいね あと乗り心地ってどうなの セダンと比べてさ 高いと酔いやすいとかないの 妻がそういうの敏感でさ 俺は全然平気なんだけど えっプリウスも見た目変わったんだ あれかっこよくなったよね 前のはちょっとあれだったけど 今のはいいじゃん スポーティで""",
        "duration_minutes": 15,
        "created_at": datetime.now()
    },
    {
        "interaction_id": str(uuid.uuid4()),
        "customer_id": "C003",
        "interaction_date": date(2026, 3, 22),
        "interaction_type": "来店",
        "sales_rep": "山本 美咲",
        "transcript": """あ初めまして田中です えっと今日車探しに来たんですけど 実は車買うの初めてで全然わからなくて すいません何聞いていいかもわからない状態で えっとですね今まで車持ってなかったんですけど 最近会社が週2出社になって通勤で使えたらいいなと思って 今カーシェアとか使ってたんですけど週末取れないこと多くて彼女に会いに行くのにちょっと困ってて そう彼女が千葉に住んでてそこまで行くのに電車だと結構かかるんですよね 予算はですねえっと150から200ちょい万くらいで考えてて 駐車場代が月3万するんで車自体はあんま高くできないんですよ 彼女はSUVがいいって言うんですけど自分は正直よくわかんなくて かっこよければなんでもいいかなみたいな 適当ですよね すいません あと来年あたり結婚とかも考えてて まあまだプロポーズしてないんですけど だから子供とか考えるとまた変わるのかなとは思うんですけど 今はとりあえず2人で使えればいいかなって ヴェゼルってなんですか あホンダの そうなんですか人気なんですね 見た目はいい感じですね あ中古であるんですか そっか新車じゃなくてもいいのか 全然考えてなかったです いやほんと何もわかんなくて すいません あの燃費っていいんですか やっぱり毎月のガソリン代とか気になるんで まあ通勤とあと週末に彼女のとこ行くくらいなんで そんな距離乗らないかもですけど あそうなんですかハイブリッドってそんなに燃費いいんですね へえ 色は何色があるんですか 彼女に聞いてみないとあれですけど 自分は黒とか紺とかがいいかな 汚れは目立ちますかね まあ洗えばいいか""",
        "duration_minutes": 10,
        "created_at": datetime.now()
    },
    {
        "interaction_id": str(uuid.uuid4()),
        "customer_id": "C004",
        "interaction_date": date(2026, 3, 23),
        "interaction_type": "来店",
        "sales_rep": "田村 直樹",
        "transcript": """お忙しいところありがとうございます渡辺です えっと今ボルボのXC60乗ってるんですけど リースがもうすぐ終わるんですね 2019年式で走行距離は4万キロくらいかな特に不満はないんですけど 再リースするか買い取るか新しいのにするか迷っていて それでいろいろ見てみようかなと 主人は別で車持ってるんですけどBMWの 家族で出かける時は私の車使うこと多いんですよね なぜか広いからかな 子供が2人いて中2と小5なんですけど 上の子がテニス部で荷物がすごいんですよ ラケット何本も持ってくし遠征とか行くと大荷物で 安全性は絶対妥協したくないですね 子供乗せる車なんで 前にボルボにしたのもそれが理由で あのボルボって安全性能いいじゃないですか 衝突試験とかでも評価高くて でも最近周りでレクサス乗ってる人多くて ちょっと気になってて RXとかNXとか 見た目も素敵だなって 予算は400万から600万くらいで考えてます 中古でも全然いいんですけど やっぱり安全装備は最新がいいのかなとも思うし 主人は好きなの選べばって言うんですけど 家計管理してるの私なんでそんな気軽に言わないでって感じですよね は結局ボルボかレクサスかって感じなんですけど 他にもおすすめあったりしますか ボルボの良さはわかってるんですけど なんていうか控えめな上質さっていうか 派手すぎないところが好きで でも周りがみんなレクサスだとちょっとねえ 見劣りするって言ったらあれですけど あとディーラーの対応とかも気になりますね 今のボルボのディーラーさんはすごく丁寧で満足してるんですけど""",
        "duration_minutes": 13,
        "created_at": datetime.now()
    }
]

# DataFrameに変換して保存
interactions_df = spark.createDataFrame(interactions_data)
interactions_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FULL_SCHEMA}.customer_interactions")

print(f"✓ 商談録音データを {FULL_SCHEMA}.customer_interactions に投入しました（{len(interactions_data)}件）")
display(spark.table(f"{FULL_SCHEMA}.customer_interactions").select("customer_id", "interaction_date", "duration_minutes"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 車両在庫データ投入

# COMMAND ----------

# 車両在庫データ
vehicles_data = [
    {
        "vehicle_id": "V001",
        "make": "トヨタ",
        "model": "シエンタ",
        "year": 2023,
        "price": 2280000,
        "body_type": "ミニバン",
        "fuel_type": "ハイブリッド",
        "mileage": 15000,
        "color": "ホワイトパールクリスタルシャイン",
        "features": ["Toyota Safety Sense", "3列シート", "低床設計", "両側電動スライドドア", "パワーバックドア"],
        "image_path": "sienta.jpg",
        "description": "コンパクトながら3列シートを備えた使いやすいミニバン。低床設計でお年寄りやお子様の乗り降りも楽々。最新の安全装備を標準搭載。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V002",
        "make": "ホンダ",
        "model": "フリード",
        "year": 2022,
        "price": 2150000,
        "body_type": "ミニバン",
        "fuel_type": "ハイブリッド",
        "mileage": 22000,
        "color": "プラチナホワイトパール",
        "features": ["Honda SENSING", "3列シート", "両側電動スライドドア", "低床フロア", "シートアレンジ多彩"],
        "image_path": "freed.jpg",
        "description": "「ちょうどいい」サイズの3列シートミニバン。Honda SENSINGによる先進安全装備と、多彩なシートアレンジが魅力。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V003",
        "make": "トヨタ",
        "model": "ヴォクシー",
        "year": 2022,
        "price": 2980000,
        "body_type": "ミニバン",
        "fuel_type": "ハイブリッド",
        "mileage": 28000,
        "color": "ブラック",
        "features": ["Toyota Safety Sense", "7人乗り", "両側電動スライドドア", "クールなデザイン"],
        "image_path": "voxy.jpg",
        "description": "スタイリッシュなデザインと広い室内空間を両立。ファミリーカーとしての実用性と、所有する喜びを感じられる一台。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V004",
        "make": "トヨタ",
        "model": "アルファード",
        "year": 2021,
        "price": 4280000,
        "body_type": "ミニバン",
        "fuel_type": "ハイブリッド",
        "mileage": 35000,
        "color": "パールホワイト",
        "features": ["Toyota Safety Sense", "本革シート", "後席モニター", "JBLプレミアムサウンド", "エグゼクティブパワーシート"],
        "image_path": "alphard.jpg",
        "description": "最上級のおもてなし空間を提供するラグジュアリーミニバン。高級感あふれる内装と圧倒的な存在感。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V005",
        "make": "トヨタ",
        "model": "ハリアー",
        "year": 2023,
        "price": 3980000,
        "body_type": "SUV",
        "fuel_type": "ハイブリッド",
        "mileage": 12000,
        "color": "プレシャスブラックパール",
        "features": ["Toyota Safety Sense", "パノラマルーフ", "JBLプレミアムサウンド", "本革シート", "電動リアゲート"],
        "image_path": "harrier.jpg",
        "description": "エレガントなデザインと走りの質感を兼ね備えたプレミアムSUV。都会にも自然にも映える洗練されたスタイル。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V006",
        "make": "ホンダ",
        "model": "ヴェゼル",
        "year": 2023,
        "price": 2180000,
        "body_type": "SUV",
        "fuel_type": "ハイブリッド",
        "mileage": 8000,
        "color": "クリスタルブラックパール",
        "features": ["Honda SENSING", "広い荷室", "後席フラット", "e:HEV", "ワンタッチウォークスルー"],
        "image_path": "vezel.jpg",
        "description": "コンパクトSUVのベストセラー。見た目のカッコよさと使いやすさを両立。e:HEVによる低燃費も魅力。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V007",
        "make": "トヨタ",
        "model": "プリウス",
        "year": 2023,
        "price": 3200000,
        "body_type": "セダン",
        "fuel_type": "ハイブリッド",
        "mileage": 10000,
        "color": "アッシュ",
        "features": ["Toyota Safety Sense", "最新ハイブリッドシステム", "スポーティデザイン", "低燃費", "先進コックピット"],
        "image_path": "prius.jpg",
        "description": "生まれ変わった新型プリウス。スポーティで流麗なデザインと、圧倒的な燃費性能を両立。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V008",
        "make": "ホンダ",
        "model": "N-BOX",
        "year": 2023,
        "price": 1680000,
        "body_type": "軽自動車",
        "fuel_type": "ガソリン",
        "mileage": 5000,
        "color": "プラチナホワイトパール",
        "features": ["Honda SENSING", "広い室内", "低床フロア", "スライドドア", "後席スーパースライド"],
        "image_path": "nbox.jpg",
        "description": "軽自動車販売台数No.1の実力。軽とは思えない広さと使いやすさ。安全装備も充実。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V009",
        "make": "レクサス",
        "model": "RX",
        "year": 2022,
        "price": 5800000,
        "body_type": "SUV",
        "fuel_type": "ハイブリッド",
        "mileage": 18000,
        "color": "ソニッククォーツ",
        "features": ["Lexus Safety System+", "マークレビンソンサウンド", "本革シート", "パノラマルーフ", "おもてなしインテリア"],
        "image_path": "lexus_rx.jpg",
        "description": "レクサスを代表するラグジュアリーSUV。最高級の走りとおもてなし空間を提供。所有する喜びを感じられる一台。",
        "status": "在庫あり",
        "created_at": datetime.now()
    },
    {
        "vehicle_id": "V010",
        "make": "ボルボ",
        "model": "XC60",
        "year": 2023,
        "price": 5200000,
        "body_type": "SUV",
        "fuel_type": "マイルドハイブリッド",
        "mileage": 15000,
        "color": "クリスタルホワイトパール",
        "features": ["IntelliSafe", "本革シート", "パノラミックサンルーフ", "Bowers & Wilkinsサウンド", "アドバンスドエアクリーナー"],
        "image_path": "volvo_xc60.jpg",
        "description": "世界最高水準の安全性能を誇るプレミアムSUV。スカンジナビアンデザインと先進安全技術の融合。",
        "status": "在庫あり",
        "created_at": datetime.now()
    }
]

# DataFrameに変換して保存
vehicles_df = spark.createDataFrame(vehicles_data)
vehicles_df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{FULL_SCHEMA}.vehicle_inventory")

print(f"✓ 車両在庫データを {FULL_SCHEMA}.vehicle_inventory に投入しました（{len(vehicles_data)}件）")
display(spark.table(f"{FULL_SCHEMA}.vehicle_inventory").select("vehicle_id", "make", "model", "year", "price"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 画像ファイルのアップロード
# MAGIC
# MAGIC 以下のセルで、ローカルの `_images/` フォルダからボリュームに画像をアップロードします。

# COMMAND ----------

# 画像ファイルのコピー（Workspace内の_imagesフォルダからVolumeへ）
import os
import shutil

# 画像ソースパス（このノートブックと同じ階層にある_imagesフォルダを想定）
# ノートブックがWorkspace上にある場合、画像もWorkspaceにアップロードしておく必要があります
workspace_images_path = "/Workspace/Users/konomi.omae@databricks.com/03_External_Work/20260406_car_recommend_agent/_images"

# Volumeの画像パス
volume_images_path = VOLUME_PATH

# 画像ファイル一覧
required_images = [
    "sienta.jpg",
    "freed.jpg",
    "voxy.jpg",
    "alphard.jpg",
    "harrier.jpg",
    "vezel.jpg",
    "prius.jpg",
    "nbox.jpg",
    "lexus_rx.jpg",
    "volvo_xc60.jpg"
]

print(f"画像のコピー元: {workspace_images_path}")
print(f"画像のコピー先: {volume_images_path}")
print(f"\n必要な画像ファイル:")
for img in required_images:
    print(f"  - {img}")

# COMMAND ----------

# 実際にコピーを実行（Workspace → Volume）
# 注: Workspaceのファイルに直接アクセスするには dbutils を使用

try:
    # Volumeディレクトリの存在確認（00_configで作成済み）
    dbutils.fs.ls(volume_images_path)
    print(f"✓ Volume path accessible: {volume_images_path}")
except Exception as e:
    print(f"Volume path check failed: {e}")

# Workspace上の画像をVolumeにコピー（shutil使用: dbutils.fs.cpはWorkspaceパスに非対応）
import shutil
import os

copied_count = 0
missing_images = []

for img_name in required_images:
    src_path = f"{workspace_images_path}/{img_name}"
    dest_path = f"/Volumes/{CATALOG}/{SCHEMA}/images/{img_name}"

    try:
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Source not found: {src_path}")
        shutil.copy2(src_path, dest_path)
        print(f"✓ Copied: {img_name}")
        copied_count += 1
    except Exception as e:
        print(f"✗ Missing: {img_name} - {str(e)[:80]}")
        missing_images.append(img_name)

print(f"\n=== 結果 ===")
print(f"コピー成功: {copied_count}/{len(required_images)}")
if missing_images:
    print(f"不足画像: {missing_images}")
    print("\n※ 不足している画像はカーセンサー等から取得してWorkspaceにアップロードしてください")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. データ確認

# COMMAND ----------

print("=== 投入データの確認 ===\n")

# 顧客
print("【顧客データ】")
display(spark.sql(f"SELECT customer_id, name, age, occupation, budget_min, budget_max FROM {FULL_SCHEMA}.customers"))

# COMMAND ----------

# 商談録音
print("【商談録音データ】")
display(spark.sql(f"""
    SELECT
        c.customer_id,
        i.interaction_date,
        i.sales_rep,
        i.duration_minutes,
        LEFT(i.transcript, 100) as transcript_preview
    FROM {FULL_SCHEMA}.customer_interactions i
    JOIN {FULL_SCHEMA}.customers c ON i.customer_id = c.customer_id
"""))

# COMMAND ----------

# 車両在庫
print("【車両在庫データ】")
display(spark.sql(f"""
    SELECT
        vehicle_id,
        make,
        model,
        year,
        FORMAT_NUMBER(price, 0) as price_formatted,
        body_type,
        fuel_type
    FROM {FULL_SCHEMA}.vehicle_inventory
    ORDER BY price
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 次のステップ
# MAGIC
# MAGIC データ投入が完了しました。次は：
# MAGIC 1. `02_ai_processing` ノートブックでAIによるインサイト抽出を実行
# MAGIC 2. または、アプリケーションからAPIでデータを参照

# COMMAND ----------

# MAGIC %md
# MAGIC ## （参考）AIインサイト抽出のサンプルクエリ
# MAGIC
# MAGIC 以下は、Foundation Model APIを使ってインサイトを抽出するサンプルです。

# COMMAND ----------

# サンプル: 山田優子さんの商談からインサイトを抽出
sample_transcript = spark.sql(f"""
    SELECT transcript
    FROM {FULL_SCHEMA}.customer_interactions
    WHERE customer_id = 'C001'
""").first()["transcript"]

print("=== 商談テキスト（サンプル）===")
print(sample_transcript[:500] + "...")

# COMMAND ----------

# AI Functionsを使ったインサイト抽出の例
# 注: 実行するにはFoundation Model APIへのアクセス権が必要

sample_query = f"""
SELECT ai_query(
    '{LLM_MODEL}',
    CONCAT(
        '以下の商談録音テキストから、顧客の深層ニーズを分析してください。',
        '\\n\\n【商談テキスト】\\n',
        transcript,
        '\\n\\n【出力形式】',
        '\\n- ペルソナ要約: ',
        '\\n- 深層ニーズ（3つ）: ',
        '\\n- 印象的な発言: ',
        '\\n- 購入緊急度: '
    )
) as insight
FROM {FULL_SCHEMA}.customer_interactions
WHERE customer_id = 'C001'
"""

print("=== AIインサイト抽出クエリ ===")
print(sample_query)

# 実行する場合は以下のコメントを解除
# display(spark.sql(sample_query))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. UCメタデータ設定（Genie最適化）
# MAGIC
# MAGIC テーブル説明・カラムコメント・NOT NULL制約・PK/FK・認定済みタグを設定します。
# MAGIC GenieがテーブルのデータとリレーションをAIで解釈するために重要な設定です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-1. customers テーブル

# COMMAND ----------

certified_tag = 'system.Certified'
table_name = f"{FULL_SCHEMA}.customers"

# テーブルコメント
spark.sql(f'''COMMENT ON TABLE {table_name} IS
"テーブル名: customers / 顧客マスタ
説明: IDOMの見込み顧客情報を管理するマスタテーブル。年齢・職業・家族構成・現在の乗車・予算・重視ポイント・背景情報を保持し、AIによる推薦・トークスクリプト生成の基盤データとなる。"
''')

# カラムコメント
column_comments = {
    "customer_id":        "顧客を一意に識別するID（C001〜）",
    "name":               "顧客氏名（苗字 + 名前）",
    "age":                "顧客の年齢（歳）",
    "gender":             "性別（男性 / 女性）",
    "occupation":         "職業・役職",
    "address":            "居住地（都道府県・市区町村）",
    "family_structure":   "家族構成の詳細（同居家族の年齢・職業・特記事項を含む）",
    "current_vehicle":    "現在乗っている車のメーカー・モデル・年式・走行距離",
    "budget_min":         "購入予算の下限（円）",
    "budget_max":         "購入予算の上限（円）",
    "preferences":        "車選びで重視するポイント（安全・燃費・積載量・デザインなど）",
    "background":         "商談背景・生活状況の詳細テキスト（AIによる深層ニーズ分析に使用）",
    "created_at":         "レコード作成日時",
}

for col, cmt in column_comments.items():
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{cmt}'")

# NOT NULL制約
for col in ["customer_id", "name"]:
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")

# 主キー
spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS pk_customers")
spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_customers PRIMARY KEY (customer_id)")

# 認定済みタグ
try:
    spark.sql(f"ALTER TABLE {table_name} SET TAGS ('{certified_tag}')")
    print(f"✓ customers: 認定済みタグ追加完了")
except Exception as e:
    print(f"△ customers: タグ追加スキップ（{e}）")

print(f"✓ customers: メタデータ設定完了")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-2. vehicle_inventory テーブル

# COMMAND ----------

table_name = f"{FULL_SCHEMA}.vehicle_inventory"

spark.sql(f'''COMMENT ON TABLE {table_name} IS
"テーブル名: vehicle_inventory / 車両在庫テーブル
説明: IDOM取扱い車両の在庫情報を管理するテーブル。メーカー・モデル・年式・価格・ボディタイプ・燃料種別・走行距離・カラー・装備・画像パス・説明文・在庫ステータスを保持する。推薦エンジンおよびGenie検索の対象テーブル。"
''')

column_comments = {
    "vehicle_id":     "車両を一意に識別するID（V001〜）",
    "make":           "メーカー名（例：トヨタ、ホンダ、レクサス、ボルボ）",
    "model":          "車種名・モデル名（例：シエンタ、ヴェゼル、NX）",
    "year":           "製造年（西暦）",
    "price":          "販売価格（円・税込）",
    "body_type":      "ボディタイプ（SUV / ミニバン / セダン / 軽自動車）",
    "fuel_type":      "燃料種別（ハイブリッド / ガソリン / マイルドハイブリッド / EV）",
    "mileage":        "走行距離（km）",
    "color":          "外装カラー名",
    "features":       "主な装備・特徴のリスト（安全システム・内装・オプション等）",
    "image_path":     "車両画像のファイル名（/api/images/ 配下で提供）",
    "description":    "車両の説明文（販売トーク・特徴の要約テキスト）",
    "status":         "在庫ステータス（在庫あり / 商談中 / 売約済み）",
    "created_at":     "レコード作成日時",
}

for col, cmt in column_comments.items():
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{cmt}'")

for col in ["vehicle_id", "make", "model", "price", "status"]:
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS pk_vehicle_inventory")
spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_vehicle_inventory PRIMARY KEY (vehicle_id)")

try:
    spark.sql(f"ALTER TABLE {table_name} SET TAGS ('{certified_tag}')")
    print(f"✓ vehicle_inventory: 認定済みタグ追加完了")
except Exception as e:
    print(f"△ vehicle_inventory: タグ追加スキップ（{e}）")

print(f"✓ vehicle_inventory: メタデータ設定完了")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-3. customer_interactions テーブル

# COMMAND ----------

table_name = f"{FULL_SCHEMA}.customer_interactions"

spark.sql(f'''COMMENT ON TABLE {table_name} IS
"テーブル名: customer_interactions / 商談録音テキストテーブル
説明: 来店顧客との商談内容を記録するテーブル。音声認識で書き起こした商談トランスクリプト・担当営業・来店日・商談時間を保持する。AIによる顧客インサイト抽出（customer_insights）の元データとなる。"
''')

column_comments = {
    "interaction_id":    "商談記録を一意に識別するID（UUID）",
    "customer_id":       "顧客ID（customersテーブルのcustomer_idと紐づくFK）",
    "interaction_date":  "商談日（来店日）",
    "interaction_type":  "商談種別（来店 / 電話 / オンライン）",
    "sales_rep":         "担当営業担当者名",
    "transcript":        "商談の書き起こしテキスト（音声認識そのまま、話者識別なし）",
    "duration_minutes":  "商談時間（分）",
    "created_at":        "レコード作成日時",
}

for col, cmt in column_comments.items():
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{cmt}'")

for col in ["interaction_id", "customer_id"]:
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS pk_customer_interactions")
spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_customer_interactions PRIMARY KEY (interaction_id)")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_interactions_customer")
spark.sql(f"""ALTER TABLE {table_name}
ADD CONSTRAINT fk_interactions_customer
FOREIGN KEY (customer_id) REFERENCES {FULL_SCHEMA}.customers(customer_id)""")

try:
    spark.sql(f"ALTER TABLE {table_name} SET TAGS ('{certified_tag}')")
    print(f"✓ customer_interactions: 認定済みタグ追加完了")
except Exception as e:
    print(f"△ customer_interactions: タグ追加スキップ（{e}）")

print(f"✓ customer_interactions: メタデータ設定完了")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-4. customer_insights テーブル

# COMMAND ----------

table_name = f"{FULL_SCHEMA}.customer_insights"

spark.sql(f'''COMMENT ON TABLE {table_name} IS
"テーブル名: customer_insights / 顧客インサイトテーブル
説明: 商談録音テキストをAIで分析して生成した顧客インサイトを保持するテーブル。ペルソナ要約・深層ニーズ・印象的な発言・懸念点・重視ポイント・ライフステージ・購買緊急度・信頼スコアを管理する。Genieによる顧客理解深化に活用。"
''')

column_comments = {
    "insight_id":              "インサイトレコードを一意に識別するID（UUID）",
    "customer_id":             "顧客ID（customersテーブルのcustomer_idと紐づくFK）",
    "interaction_id":          "元となった商談ID（customer_interactionsテーブルのinteraction_idと紐づくFK）",
    "persona_summary":         "AIが生成した顧客ペルソナの要約テキスト（生活背景・価値観・行動特性）",
    "deep_needs":              "AIが抽出した深層ニーズ（表面的な希望の背後にある本質的ニーズ）",
    "key_quotes":              "商談中の印象的な発言リスト（JSON配列形式）",
    "concerns":                "顧客の懸念点・不安要素",
    "preferences_extracted":   "AIが抽出した具体的な車選びの優先事項",
    "life_stage":              "ライフステージ分類（例：子育て中ファミリー・定年前シニア・若手社会人）",
    "purchase_urgency":        "購買緊急度（高 / 中 / 低）",
    "confidence_score":        "インサイト分析の信頼スコア（0.0〜1.0）",
    "processed_at":            "インサイト生成日時",
    "model_used":              "使用したLLMモデル名",
}

for col, cmt in column_comments.items():
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{cmt}'")

for col in ["insight_id", "customer_id"]:
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS pk_customer_insights")
spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_customer_insights PRIMARY KEY (insight_id)")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_insights_customer")
spark.sql(f"""ALTER TABLE {table_name}
ADD CONSTRAINT fk_insights_customer
FOREIGN KEY (customer_id) REFERENCES {FULL_SCHEMA}.customers(customer_id)""")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_insights_interaction")
spark.sql(f"""ALTER TABLE {table_name}
ADD CONSTRAINT fk_insights_interaction
FOREIGN KEY (interaction_id) REFERENCES {FULL_SCHEMA}.customer_interactions(interaction_id)""")

try:
    spark.sql(f"ALTER TABLE {table_name} SET TAGS ('{certified_tag}')")
    print(f"✓ customer_insights: 認定済みタグ追加完了")
except Exception as e:
    print(f"△ customer_insights: タグ追加スキップ（{e}）")

print(f"✓ customer_insights: メタデータ設定完了")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-5. recommendations テーブル

# COMMAND ----------

table_name = f"{FULL_SCHEMA}.recommendations"

spark.sql(f'''COMMENT ON TABLE {table_name} IS
"テーブル名: recommendations / 車両推薦結果テーブル
説明: 顧客ごとにAIが生成した車両推薦結果を保持するテーブル。推薦車両リスト（JSON）・マッチスコア・推薦理由・営業トークスクリプト・生成日時・使用モデルを管理する。アプリのGET /recommendations エンドポイントがこのテーブルを参照（UC読み取りキャッシュパターン）。"
''')

column_comments = {
    "recommendation_id":    "推薦レコードを一意に識別するID（UUID）",
    "customer_id":          "顧客ID（customersテーブルのcustomer_idと紐づくFK）",
    "recommendations_json": "推薦車両リストのJSONテキスト（vehicle情報・match_score・reason を含む配列）",
    "talk_script":          "AI生成の営業トークスクリプト（Markdown形式・Format B：第1位/第2位/第3位構成）",
    "generated_at":         "推薦データの生成日時",
    "model_used":           "推薦生成に使用したLLMモデル名",
}

for col, cmt in column_comments.items():
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{cmt}'")

for col in ["recommendation_id", "customer_id"]:
    spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS pk_recommendations")
spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_recommendations PRIMARY KEY (recommendation_id)")

spark.sql(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS fk_recommendations_customer")
spark.sql(f"""ALTER TABLE {table_name}
ADD CONSTRAINT fk_recommendations_customer
FOREIGN KEY (customer_id) REFERENCES {FULL_SCHEMA}.customers(customer_id)""")

try:
    spark.sql(f"ALTER TABLE {table_name} SET TAGS ('{certified_tag}')")
    print(f"✓ recommendations: 認定済みタグ追加完了")
except Exception as e:
    print(f"△ recommendations: タグ追加スキップ（{e}）")

print(f"✓ recommendations: メタデータ設定完了")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6-6. 設定結果の確認

# COMMAND ----------

print("=== UCメタデータ設定確認 ===\n")
for tbl in ["customers", "vehicle_inventory", "customer_interactions", "customer_insights", "recommendations"]:
    full = f"{FULL_SCHEMA}.{tbl}"
    result = spark.sql(f"DESCRIBE EXTENDED {full}").filter("col_name IN ('Comment', 'Table Properties')")
    print(f"【{tbl}】")
    result.show(truncate=80)
