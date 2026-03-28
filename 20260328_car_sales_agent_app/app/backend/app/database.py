"""Database connection module using Databricks REST API via httpx."""

import os
from typing import Any, Optional

from app.config import get_settings, get_databricks_host, is_databricks_app


class DatabasePool:
    """Database connection manager using Databricks REST API."""

    def __init__(self):
        self._client = None
        self._demo_mode: bool = False
        self._initialized: bool = False
        self._warehouse_id: str = ""
        self._host: str = ""

    async def initialize(self) -> None:
        """Initialize database connection."""
        if self._initialized:
            return

        settings = get_settings()
        self._host = get_databricks_host()
        self._warehouse_id = settings.databricks_warehouse_id

        if not self._host or not self._warehouse_id:
            print(f"Databricks not configured (host={bool(self._host)}, warehouse={bool(self._warehouse_id)}) - using demo mode")
            self._demo_mode = True
            self._initialized = True
            return

        try:
            from databricks.sdk import WorkspaceClient
            self._client = WorkspaceClient()
            self._initialized = True
            print(f"Database initialized: host={self._host}, warehouse={self._warehouse_id}")
        except Exception as e:
            print(f"WorkspaceClient init failed: {e} - using demo mode")
            self._demo_mode = True
            self._initialized = True

    def _get_auth_headers(self) -> dict:
        """Get authentication headers for Databricks REST API."""
        # Use cached SDK client's config.authenticate() - works for PAT, OAuth, M2M, Databricks Apps
        if self._client:
            try:
                auth_headers = self._client.config.authenticate()
                if auth_headers and "Authorization" in auth_headers:
                    return dict(auth_headers)
            except Exception as e:
                print(f"SDK auth failed: {e}")

        # Fallback: DATABRICKS_TOKEN env var (PAT)
        token = os.environ.get("DATABRICKS_TOKEN", "")
        if token:
            return {"Authorization": f"Bearer {token}"}

        return {}

    async def execute_query(self, query: str, params: Optional[dict] = None) -> list[dict[str, Any]]:
        """Execute SQL query and return results as list of dicts."""
        if self._demo_mode:
            return self._get_demo_data(query)

        if not self._initialized:
            await self.initialize()
            if self._demo_mode:
                return self._get_demo_data(query)

        try:
            import httpx

            headers = self._get_auth_headers()
            if not headers:
                print("No auth headers available - using demo mode for this query")
                return self._get_demo_data(query)

            headers["Content-Type"] = "application/json"

            payload = {
                "statement": query,
                "warehouse_id": self._warehouse_id,
                "format": "JSON_ARRAY",
                "wait_timeout": "30s",
            }

            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(
                    f"{self._host}/api/2.0/sql/statements/",
                    json=payload,
                    headers=headers,
                )

            if resp.status_code != 200:
                print(f"Query HTTP error: {resp.status_code} - {resp.text[:200]}")
                print(f"Query was: {query[:200]}")
                return self._get_demo_data(query)

            response = resp.json()
            status = response.get("status", {})
            state = status.get("state", "")

            if state == "FAILED":
                error = status.get("error", {})
                error_msg = error.get("message", "Unknown error") if error else "Unknown error"
                print(f"Query failed: {error_msg}")
                print(f"Query was: {query[:200]}")
                return self._get_demo_data(query)

            result = response.get("result", {})
            data_array = result.get("data_array") or []

            if not data_array:
                return []

            manifest = response.get("manifest", {})
            schema = manifest.get("schema", {})
            columns = schema.get("columns", [])

            rows_out = []
            for row in data_array:
                record = {}
                for col_def, val in zip(columns, row):
                    col_name = col_def.get("name", "")
                    type_name = col_def.get("type_name", "STRING")
                    if val is None:
                        record[col_name] = None
                    elif type_name in ("INT", "INTEGER", "LONG", "BIGINT"):
                        try:
                            record[col_name] = int(val)
                        except (ValueError, TypeError):
                            record[col_name] = val
                    elif type_name in ("FLOAT", "DOUBLE", "DECIMAL"):
                        try:
                            record[col_name] = float(val)
                        except (ValueError, TypeError):
                            record[col_name] = val
                    else:
                        record[col_name] = val
                rows_out.append(record)

            print(f"Query OK: {len(rows_out)} rows returned")
            return rows_out

        except Exception as e:
            print(f"Query execution failed: {e}")
            print(f"Query was: {query[:200]}")
            return self._get_demo_data(query)

    def _get_demo_data(self, query: str) -> list[dict[str, Any]]:
        """Return demo data when database is not available."""
        query_lower = query.lower()

        if "customers" in query_lower and "recommendations" not in query_lower and "insights" not in query_lower and "interactions" not in query_lower:
            all_customers = [
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
                    "background": "子供2人の習い事送迎と義母の病院送迎担当。現在のセレナは8年目で走行12万km超え。",
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
                    "background": "来年定年。週末ゴルフが趣味。維持費を意識しつつ格を求める。",
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
                    "budget_max": 2800000,
                    "preferences": "彼女がSUV希望、かっこよければOK、実用的",
                    "background": "初めての車購入。彼女の希望はSUV。来年結婚を検討中。",
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
                    "background": "リース満了が近い。長女テニス部で荷物が多い。レクサスに関心あり。",
                },
            ]
            # Filter by customer_id if WHERE clause present
            import re as _re
            m = _re.search(r"customer_id\s*=\s*'(\w+)'", query_lower)
            if m:
                cid = m.group(1).upper()
                return [c for c in all_customers if c["customer_id"] == cid]
            return all_customers

        if "vehicle_inventory" in query_lower or "vehicles" in query_lower:
            return [
                {
                    "vehicle_id": "V001", "make": "トヨタ", "model": "シエンタ", "year": 2023,
                    "price": 2280000, "body_type": "ミニバン", "fuel_type": "ハイブリッド", "mileage": 15000,
                    "color": "ホワイトパール", "features": "Toyota Safety Sense,3列シート,低床設計,両側電動スライドドア",
                    "image_url": "/api/images/sienta.jpg", "status": "在庫あり",
                    "description": "7人乗りコンパクトミニバン。低床で乗り降りしやすい。",
                },
                {
                    "vehicle_id": "V002", "make": "ホンダ", "model": "フリード", "year": 2023,
                    "price": 2050000, "body_type": "ミニバン", "fuel_type": "ハイブリッド", "mileage": 12000,
                    "color": "プラチナホワイトパール", "features": "Honda SENSING,e:HEV,コンパクト6人乗り",
                    "image_url": "/api/images/freed.jpg", "status": "在庫あり",
                    "description": "コンパクトで取り回しやすいミニバン。",
                },
                {
                    "vehicle_id": "V003", "make": "ホンダ", "model": "ヴェゼル", "year": 2023,
                    "price": 2650000, "body_type": "SUV", "fuel_type": "ハイブリッド", "mileage": 8000,
                    "color": "プレミアムサンライトホワイト", "features": "Honda SENSING,e:HEV,9インチナビ",
                    "image_url": "/api/images/vezel.jpg", "status": "在庫あり",
                    "description": "スタイリッシュなコンパクトSUV。",
                },
                {
                    "vehicle_id": "V004", "make": "トヨタ", "model": "ハリアー", "year": 2022,
                    "price": 3850000, "body_type": "SUV", "fuel_type": "ハイブリッド", "mileage": 22000,
                    "color": "プレミアムホワイトパール", "features": "Toyota Safety Sense,JBL,ムーンルーフ,本革シート",
                    "image_url": "/api/images/harrier.jpg", "status": "在庫あり",
                    "description": "上質なプレミアムSUV。ゴルフバッグ積載可能。",
                },
                {
                    "vehicle_id": "V005", "make": "トヨタ", "model": "プリウス", "year": 2023,
                    "price": 3290000, "body_type": "セダン", "fuel_type": "ハイブリッド", "mileage": 5000,
                    "color": "エモーショナルレッドII", "features": "Toyota Safety Sense,パノラマルーフ,新デザイン",
                    "image_url": "/api/images/prius.jpg", "status": "在庫あり",
                    "description": "新世代の低燃費セダン。洗練されたデザイン。",
                },
                {
                    "vehicle_id": "V006", "make": "レクサス", "model": "NX", "year": 2022,
                    "price": 5800000, "body_type": "SUV", "fuel_type": "ハイブリッド", "mileage": 18000,
                    "color": "ソニックチタニウム", "features": "Lexus Safety System+,マークレビンソン,デジタルアウターミラー,本革",
                    "image_url": "/api/images/lexus_rx.jpg", "status": "在庫あり",
                    "description": "レクサスの上質SUV。最先端安全装備と音響システム。",
                },
                {
                    "vehicle_id": "V007", "make": "ボルボ", "model": "XC40", "year": 2022,
                    "price": 5200000, "body_type": "SUV", "fuel_type": "ハイブリッド", "mileage": 25000,
                    "color": "クリスタルホワイトパール", "features": "Pilot Assist,Harman Kardon,全周囲カメラ,パノラマルーフ",
                    "image_url": "/api/images/volvo_xc60.jpg", "status": "在庫あり",
                    "description": "北欧安全性の最高水準。洗練されたプレミアムSUV。",
                },
                {
                    "vehicle_id": "V008", "make": "トヨタ", "model": "アルファード", "year": 2023,
                    "price": 7200000, "body_type": "ミニバン", "fuel_type": "ハイブリッド", "mileage": 3000,
                    "color": "ホワイトパールクリスタルシャイン", "features": "Toyota Safety Sense,JBL,本革エグゼクティブシート,4WD",
                    "image_url": "/api/images/alphard.jpg", "status": "在庫あり",
                    "description": "最上級ミニバン。VIPグレードの快適性。",
                },
                {
                    "vehicle_id": "V009", "make": "スバル", "model": "フォレスター", "year": 2023,
                    "price": 3150000, "body_type": "SUV", "fuel_type": "ハイブリッド", "mileage": 10000,
                    "color": "クリスタルホワイトパール", "features": "EyeSight,AWD,大型ガラスルーフ,X-MODE",
                    "image_url": "/api/images/harrier.jpg", "status": "在庫あり",
                    "description": "信頼のAWDと最高の視界。アウトドア派に最適。",
                },
                {
                    "vehicle_id": "V010", "make": "BMW", "model": "3シリーズ", "year": 2022,
                    "price": 4980000, "body_type": "セダン", "fuel_type": "ガソリン", "mileage": 30000,
                    "color": "ブラックサファイア", "features": "本革シート,DriveAssist,HUD,ハーマンカードン",
                    "image_url": "/api/images/prius.jpg", "status": "在庫あり",
                    "description": "究極のドライビングマシン。プレミアムセダンの王道。",
                },
            ]

        return []

    async def close(self) -> None:
        """Close database connection."""
        self._initialized = False

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self._demo_mode


# Global database instance
db = DatabasePool()
