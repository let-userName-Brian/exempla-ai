from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HostSchema(BaseModel):
    vcenter: Optional[str]
    nics: int
    vendor: Optional[str]
    vcpus: int
    desktop_vms: int
    esx_version: str
    ht_active: bool
    cluster: Optional[str]
    dataset_id: int
    vms: int
    host_hash: Optional[str]
    cores: int
    memory_gb: int
    speed: float
    cpu_usage: float
    vram: int
    collection: Optional[str]
    cpu_model: Optional[str]
    hbas: int
    server_vms: int
    memory_usage: float
    memory: int
    model: Optional[str]
    cpus: int
    host: str
    datacenter: Optional[str]
    created_at: Optional[datetime] = None
