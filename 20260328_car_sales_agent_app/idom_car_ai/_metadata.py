from pathlib import Path

app_name = "idom-car-ai"
app_entrypoint = "idom_car_ai.backend.app:app"
app_slug = "idom_car_ai"
api_prefix = "/api"
dist_dir = Path(__file__).parent / "__dist__"