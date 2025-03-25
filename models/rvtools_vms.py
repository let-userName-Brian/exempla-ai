from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class VMSchema(BaseModel):
    vm: str
    path: Optional[str]
    created_at: Optional[datetime] = None
    vm_tools_os: Optional[str]
    consumed_mib: Optional[float]
    phys_cores_used: Optional[float]
    config_os: Optional[str]
    in_use_mib: Optional[float]
    in_use_gb: Optional[float]
    vm_hash: Optional[str]
    network: Optional[List[str]] = []
    resource_pool: Optional[str]
    is_desktop: Optional[bool] = False
    cluster: Optional[str]
    capacity_mib: Optional[List[float]] = []
    thin: Optional[List[bool]] = []
    cpus: int
    disks: int
    host: str
    switch: Optional[List[str]] = []
    powerstate: str
    nics: int
    provisioned_mib: Optional[float]
    provisioned_gb: Optional[float]
    collection: Optional[str]
    memory: int
    vcenter: Optional[str]
    datacenter: Optional[str]
    dataset_id: int
    memory_gb: Optional[int]
    phys_ram_used: Optional[float]
