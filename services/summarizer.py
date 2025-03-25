from typing import Dict, Any

def create_vm_summary_from_dict(vm_dict: Dict[str, Any]) -> str:
    power_state = vm_dict.get("powerstate", "unknown")
    power_state_str = "powered on" if power_state == "poweredOn" else power_state
    memory = vm_dict.get("memory", 0)
    memory_gb = vm_dict.get("memory_gb") or (round(memory / 1024, 2) if memory else 0)
    provisioned_mib = vm_dict.get("provisioned_mib", 0)
    provisioned_gb = vm_dict.get("provisioned_gb") or (
        provisioned_mib / 1024 if provisioned_mib else 0
    )
    in_use_mib = vm_dict.get("in_use_mib", 0)
    in_use_gb = vm_dict.get("in_use_gb") or (in_use_mib / 1024 if in_use_mib else 0)
    consumed_mib = vm_dict.get("consumed_mib", 0)
    consumed_gb = consumed_mib / 1024 if consumed_mib else 0
    thin_list = vm_dict.get("thin", []) or []
    thin_count = len([t for t in thin_list if t])
    total_disks = vm_dict.get("disks", 0)
    network_list = vm_dict.get("network", []) or []
    switch_list = vm_dict.get("switch", []) or []
    config_os = vm_dict.get("config_os")
    vm_tools_os = vm_dict.get("vm_tools_os")
    os_info = config_os or vm_tools_os or "unknown"

    summary = (
        f"VM '{vm_dict.get('vm', 'unknown')}' (hash={vm_dict.get('vm_hash', 'unknown')}), dataset {vm_dict.get('dataset_id', 'unknown')}. "
        f"It is {power_state_str} on host '{vm_dict.get('host', 'unknown')}', cluster '{vm_dict.get('cluster', 'unknown')}', in datacenter '{vm_dict.get('datacenter', 'unknown')}'. "
        f"Has {vm_dict.get('cpus', 0)} vCPUs, {memory_gb} GB memory. Provisioned ~{round(provisioned_gb, 2)} GB, in-use ~{round(in_use_gb, 2)} GB, consumed ~{round(consumed_gb, 2)} GB. "
        f"OS: {os_info}. is_desktop: {vm_dict.get('is_desktop', False)}. "
        f"Networks: {', '.join(network_list) if network_list else 'none'}. Switches: {', '.join(switch_list) if switch_list else 'none'}. "
        f"Thin-provisioned disks: {thin_count} of {total_disks}. "
        f"Resource pool: {vm_dict.get('resource_pool') or 'N/A'}. Path: {vm_dict.get('path') or 'N/A'}. "
        f"Physical cores used: {vm_dict.get('phys_cores_used') or 'unknown'}, physical RAM used: {vm_dict.get('phys_ram_used') or 'unknown'} GB. "
        f"Record created at {vm_dict.get('created_at') or 'unknown time'}. "
    )
    return summary.strip()


def create_host_summary_from_dict(host_dict: Dict[str, Any]) -> str:
    summary = (
        f"Host '{host_dict.get('host', 'unknown')}' (hash={host_dict.get('host_hash', 'unknown')}), dataset {host_dict.get('dataset_id', 'unknown')}. "
        f"Datacenter: '{host_dict.get('datacenter', 'unknown')}'. Cluster: '{host_dict.get('cluster', 'unknown')}'. "
        f"Vendor: {host_dict.get('vendor', 'unknown')}, Model: {host_dict.get('model', 'unknown')}, CPU model: {host_dict.get('cpu_model', 'unknown')}. "
        f"ESXi version: {host_dict.get('esx_version', 'unknown')}, hyper-threading: {'active' if host_dict.get('ht_active', False) else 'inactive'}. "
        f"Cores: {host_dict.get('cores', 0)}, total vCPUs: {host_dict.get('vcpus', 0)}, usage at {host_dict.get('cpu_usage', 0)}%. "
        f"Memory: {host_dict.get('memory', 0)} MB (~{host_dict.get('memory_gb', 0)} GB), usage {host_dict.get('memory_usage', 0)}%. "
        f"{host_dict.get('vms', 0)} VMs total, {host_dict.get('desktop_vms', 0)} desktop, {host_dict.get('server_vms', 0)} server. VRAM: {host_dict.get('vram', 0)} MB. "
        f"NICS: {host_dict.get('nics', 0)}, HBAs: {host_dict.get('hbas', 0)}, CPU packages: {host_dict.get('cpus', 0)}, speed: {host_dict.get('speed', 0)} MHz. "
        f"vCenter: {host_dict.get('vcenter', 'unknown')}. Created at {host_dict.get('created_at') or 'unknown time'}. "
    )
    return summary.strip()
