from .base import StaticAdapter

RUNPOD_ADAPTER = StaticAdapter(
    "runpod",
    [
        {
            "id": "runpod-a100",
            "gpu_model": "A100",
            "vram_gb": 80,
            "cpu_cores": 16,
            "ram_gb": 128,
            "storage_gb": 200,
            "region": "us-west-2",
            "zone": "us-west-2a",
            "availability": 0.65,
            "spot": True,
            "price_per_hour": 3.2,
            "tags": ["training"],
            "frameworks": ["pytorch"],
            "billing_increment_min": 10,
            "confidence": 0.6,
        }
    ],
)
