from pydantic import BaseModel
from typing import List, Dict


class HostFilterOptions(BaseModel):
    host_names: List[str] = []
    models: List[str] = []
    cpu_models: List[str] = []
    vendors: List[str] = []
    esx_versions: List[str] = []
    ht_actives: List[str] = []
    memory_gb_values: List[int] = []


class VmFilterOptions(BaseModel):
    vm_names: List[str] = []
    os_types: List[str] = []
    os_versions: List[str] = []
    power_states: List[str] = []
    apps: List[str] = []
    thin_values: List[bool] = []
    switches: List[str] = []
    networks: List[str] = []
    memory_gb_range: Dict[str, int] = {"min": 0, "max": 999999}
    in_use_mib_range: Dict[str, int] = {"min": 0, "max": 999999}


class InfrastructureFilterOptions(BaseModel):
    vcenters: List[str] = []
    datacenters: List[str] = []
    clusters: List[str] = []


class FilterOptions(BaseModel):
    host_filters: HostFilterOptions
    vm_filters: VmFilterOptions
    infrastructure_filters: InfrastructureFilterOptions
