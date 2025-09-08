from typing import Dict, Any

# 簡單的 in-memory 狀態表；若專案已有，沿用既有的
job_statuses: Dict[str, Dict[str, Any]] = {}