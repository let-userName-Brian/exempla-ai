from typing import List, Dict
from pymongo import MongoClient
from services.config import Config

cfg = Config()

def get_mongo_client() -> MongoClient:
    return MongoClient(cfg.MONGO_URI)

def fetch_vms_for_dataset(dataset_id: int) -> List[Dict]:
    client = get_mongo_client()
    db = client[cfg.MONGO_DB]
    return list(db["rvtools_vms"].find({"dataset_id": dataset_id}))

def fetch_hosts_for_dataset(dataset_id: int) -> List[Dict]:
    client = get_mongo_client()
    db = client[cfg.MONGO_DB]
    return list(db["rvtools_hosts"].find({"dataset_id": dataset_id}))
