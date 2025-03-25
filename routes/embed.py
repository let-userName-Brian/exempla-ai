from concurrent.futures import ThreadPoolExecutor
import uuid
from fastapi import APIRouter, BackgroundTasks
from services.mongo import (
    fetch_vms_for_dataset,
    fetch_hosts_for_dataset,
    get_mongo_client,
)
from services.summarizer import (
    create_host_summary_from_dict,
    create_vm_summary_from_dict,
)
from services.embedding import batch_embed_texts
from services.vector_store import batch_upsert_vectors
from datetime import datetime
from pydantic import BaseModel
from services.task_manager import task_manager

router = APIRouter()


class DatasetEmbedRequest(BaseModel):
    dataset_id: int


def process_embeddings_with_tracking(dataset_id: int, task_id: str):
    """wrapper for our internal task manager"""
    try:
        task_manager.register_task(
            task_id,
            {
                "type": "embedding",
                "dataset_id": dataset_id,
                "started_at": datetime.utcnow(),
            },
        )

        process_embeddings(dataset_id)
    except InterruptedError as e:
        mongo_client = get_mongo_client()
        embedding_status = mongo_client.exempla.embedding_status

        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "status": "interrupted",
                    "message": str(e),
                    "interrupted_at": datetime.utcnow(),
                }
            },
        )
        print(f"Task {task_id} was interrupted: {str(e)}")
    except Exception as e:
        print(f"Error in task {task_id}: {str(e)}")
    finally:
        task_manager.unregister_task(task_id)


def process_embeddings(dataset_id: int):
    mongo_client = get_mongo_client()
    embedding_status = mongo_client.exempla.embedding_status
    embedding_status.update_one(
        {"dataset_id": dataset_id},
        {
            "$set": {
                "status": "processing",
                "started_at": datetime.utcnow(),
                "progress": 0,
                "message": "Starting embedding process",
                "error": None,
                "failed_at": None,
                "processed_items": 0,
                "skipped_items": 0,
            }
        },
        upsert=True,
    )

    try:
        if task_manager.should_shutdown():
            raise InterruptedError("Embedding process interrupted by server shutdown")

        vms_raw = fetch_vms_for_dataset(dataset_id)
        hosts_raw = fetch_hosts_for_dataset(dataset_id)
        total_items = len(vms_raw) + len(hosts_raw)
        processed_items = 0
        skipped_items = 0

        print(
            f"Embedding {len(vms_raw)} VMs and {len(hosts_raw)} hosts for dataset {dataset_id}"
        )

        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "total_items": total_items,
                    "vm_count": len(vms_raw),
                    "host_count": len(hosts_raw),
                    "message": f"Processing {len(vms_raw)} VMs and {len(hosts_raw)} hosts",
                }
            },
        )

        batch_size = 20
        num_workers = 4

        # vms
        def process_vm_batch(batch):
            if task_manager.should_shutdown():
                raise InterruptedError(
                    "VM batch processing interrupted by server shutdown"
                )

            try:
                summaries = []
                ids = []
                metadata_list = []

                for vm in batch:
                    try:
                        vm_id = str(
                            vm.get("vm_hash") or vm.get("vm") or f"vm-{uuid.uuid4()}"
                        )

                        summary = create_vm_summary_from_dict(vm)
                        metadata = {
                            "dataset_id": vm.get("dataset_id"),
                            "type": "vm",
                            "vm": vm.get("vm", "unknown"),
                            "vm_hash": vm.get("vm_hash"),
                            "host": vm.get("host", "unknown"),
                            "cluster": vm.get("cluster", "unknown"),
                            "datacenter": vm.get("datacenter", "unknown"),
                            "vcenter": vm.get("vcenter"),
                            "path": vm.get("path"),
                            "resource_pool": vm.get("resource_pool"),
                            "powerstate": vm.get("powerstate", "unknown"),
                            "created_at": vm.get("created_at"),
                            "cpus": vm.get("cpus"),
                            "memory": vm.get("memory"),
                            "memory_gb": vm.get("memory_gb"),
                            "disks": vm.get("disks"),
                            "nics": vm.get("nics"),
                            "provisioned_mib": vm.get("provisioned_mib"),
                            "provisioned_gb": vm.get("provisioned_gb"),
                            "in_use_mib": vm.get("in_use_mib"),
                            "in_use_gb": vm.get("in_use_gb"),
                            "consumed_mib": vm.get("consumed_mib"),
                            "capacity_mib": vm.get("capacity_mib"),
                            "network": vm.get("network", []),
                            "switch": vm.get("switch", []),
                            "config_os": vm.get("config_os"),
                            "vm_tools_os": vm.get("vm_tools_os"),
                            "phys_cores_used": vm.get("phys_cores_used"),
                            "phys_ram_used": vm.get("phys_ram_used"),
                            "is_desktop": vm.get("is_desktop", False),
                            "thin": vm.get("thin", []),
                            "collection": vm.get("collection"),
                        }

                        summaries.append(summary)
                        ids.append(vm_id)
                        metadata_list.append(metadata)
                    except Exception as e:
                        print(f"Error preparing VM: {str(e)}")
                        continue

                if not summaries:
                    return 0, len(batch)

                embeddings = batch_embed_texts(summaries)
                batch_upsert_vectors(ids, embeddings, metadata_list)

                return len(summaries), len(batch) - len(summaries)
            except InterruptedError:
                raise
            except Exception as e:
                print(f"Error processing VM batch: {str(e)}")
                return 0, len(batch)

        # hosts
        def process_host_batch(batch):
            if task_manager.should_shutdown():
                raise InterruptedError(
                    "Host batch processing interrupted by server shutdown"
                )

            try:
                summaries = []
                ids = []
                metadata_list = []

                for host in batch:
                    try:
                        host_id = str(
                            host.get("host_hash")
                            or host.get("host")
                            or f"host-{uuid.uuid4()}"
                        )
                        
                        summary = create_host_summary_from_dict(host)
                        metadata = {
                            "dataset_id": host.get("dataset_id"),
                            "type": "host",
                            "host": host.get("host", "unknown"),
                            "host_hash": host.get("host_hash"),
                            "datacenter": host.get("datacenter", "unknown"),
                            "cluster": host.get("cluster"),
                            "vcenter": host.get("vcenter"),
                            "vendor": host.get("vendor"),
                            "model": host.get("model"),
                            "cpu_model": host.get("cpu_model"),
                            "cpus": host.get("cpus"),
                            "cores": host.get("cores"),
                            "vcpus": host.get("vcpus"),
                            "speed": host.get("speed"),
                            "memory": host.get("memory"),
                            "memory_gb": host.get("memory_gb"),
                            "nics": host.get("nics"),
                            "hbas": host.get("hbas"),
                            "cpu_usage": host.get("cpu_usage"),
                            "memory_usage": host.get("memory_usage"),
                            "vms": host.get("vms"),
                            "desktop_vms": host.get("desktop_vms"),
                            "server_vms": host.get("server_vms"),
                            "vram": host.get("vram"),
                            "esx_version": host.get("esx_version"),
                            "ht_active": host.get("ht_active"),
                            "collection": host.get("collection"),
                            "created_at": host.get("created_at"),
                        }

                        summaries.append(summary)
                        ids.append(host_id)
                        metadata_list.append(metadata)
                    except Exception as e:
                        print(f"Error preparing host: {str(e)}")
                        continue

                if not summaries:
                    return 0, len(batch)

                embeddings = batch_embed_texts(summaries)
                batch_upsert_vectors(ids, embeddings, metadata_list)
                return len(summaries), len(batch) - len(summaries)
            except InterruptedError:
                raise
            except Exception as e:
                print(f"Error processing host batch: {str(e)}")
                return 0, len(batch)

        vm_batches = [
            vms_raw[i : i + batch_size] for i in range(0, len(vms_raw), batch_size)
        ]

        if task_manager.should_shutdown():
            raise InterruptedError("Embedding process interrupted by server shutdown")

        # process batches using threads
        vm_results = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_batch = {
                executor.submit(process_vm_batch, batch): i
                for i, batch in enumerate(vm_batches)
            }

            for future in future_to_batch:
                try:
                    result = future.result()
                    vm_results.append(result)

                    batch_index = future_to_batch[future]
                    if batch_index % 5 == 0 or batch_index == len(vm_batches) - 1:
                        current_processed = sum(r[0] for r in vm_results)
                        current_skipped = sum(r[1] for r in vm_results)
                        progress_percentage = int(
                            (current_processed / total_items) * 100
                        )

                        embedding_status.update_one(
                            {"dataset_id": dataset_id},
                            {
                                "$set": {
                                    "progress": progress_percentage,
                                    "processed_items": current_processed,
                                    "skipped_items": current_skipped,
                                    "message": f"Processed {current_processed}/{total_items} items ({progress_percentage}%)",
                                }
                            },
                        )
                except Exception as e:
                    print(f"Error getting VM batch result: {str(e)}")

        vm_processed = sum(r[0] for r in vm_results)
        vm_skipped = sum(r[1] for r in vm_results)

        processed_items += vm_processed
        skipped_items += vm_skipped
        progress_percentage = int((processed_items / total_items) * 100)
        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "progress": progress_percentage,
                    "processed_items": processed_items,
                    "skipped_items": skipped_items,
                    "message": f"Processed {processed_items}/{total_items} items ({progress_percentage}%)",
                }
            },
        )

        if task_manager.should_shutdown():
            raise InterruptedError("Embedding process interrupted by server shutdown")

        host_batches = [
            hosts_raw[i : i + batch_size] for i in range(0, len(hosts_raw), batch_size)
        ]

        host_results = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_batch = {
                executor.submit(process_host_batch, batch): i
                for i, batch in enumerate(host_batches)
            }

            for future in future_to_batch:
                try:
                    result = future.result()
                    host_results.append(result)
                    batch_index = future_to_batch[future]
                    if batch_index % 5 == 0 or batch_index == len(host_batches) - 1:
                        current_processed = processed_items + sum(
                            r[0] for r in host_results
                        )
                        current_skipped = skipped_items + sum(
                            r[1] for r in host_results
                        )
                        progress_percentage = int(
                            (current_processed / total_items) * 100
                        )

                        embedding_status.update_one(
                            {"dataset_id": dataset_id},
                            {
                                "$set": {
                                    "progress": progress_percentage,
                                    "processed_items": current_processed,
                                    "skipped_items": current_skipped,
                                    "message": f"Processed {current_processed}/{total_items} items ({progress_percentage}%)",
                                }
                            },
                        )
                except Exception as e:
                    print(f"Error getting host batch result: {str(e)}")

        host_processed = sum(r[0] for r in host_results)
        host_skipped = sum(r[1] for r in host_results)
        processed_items += host_processed
        skipped_items += host_skipped
        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "progress": 100,
                    "processed_items": processed_items,
                    "skipped_items": skipped_items,
                    "message": f"Successfully embedded {processed_items}/{total_items} items ({skipped_items} skipped)",
                }
            },
        )

        print(f"Dataset {dataset_id} embedded successfully.")

    except InterruptedError as e:
        error_message = str(e)
        print(
            f"Embedding process for dataset {dataset_id} was interrupted: {error_message}"
        )

        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "status": "interrupted",
                    "error": error_message,
                    "interrupted_at": datetime.utcnow(),
                    "message": f"Embedding interrupted: {error_message}",
                }
            },
        )
        raise

    except Exception as e:
        error_message = str(e)
        print(f"Error embedding dataset {dataset_id}: {error_message}")

        embedding_status.update_one(
            {"dataset_id": dataset_id},
            {
                "$set": {
                    "status": "failed",
                    "error": error_message,
                    "failed_at": datetime.utcnow(),
                    "message": f"Embedding failed: {error_message}",
                }
            },
        )


@router.post("/")
def embed_dataset(background_tasks: BackgroundTasks, request: DatasetEmbedRequest):
    """
    Start a background task to embed the dataset:
    1. Fetch all VMs & Hosts for the given dataset_id from MongoDB
    2. Summarize them to normal text
    3. Embed the summary using the embedding model
    4. Store in Qdrant with full items metadata
    """
    dataset_id = request.dataset_id
    mongo_client = get_mongo_client()
    embedding_status = mongo_client.exempla.embedding_status

    embedding_status.update_one(
        {"dataset_id": dataset_id},
        {
            "$set": {
                "dataset_id": dataset_id,
                "status": "pending",
                "created_at": datetime.utcnow(),
                "progress": 0,
                "message": "Embedding task queued",
                "error": None,
                "failed_at": None,
            }
        },
        upsert=True,
    )
    task_id = f"embed-{dataset_id}-{uuid.uuid4()}"

    background_tasks.add_task(process_embeddings_with_tracking, dataset_id, task_id)

    return {
        "message": f"Dataset {dataset_id} embedding started in the background.",
        "status": "pending",
    }


@router.get("/{dataset_id}/status")
def get_embedding_status(dataset_id: int):
    """
    Check on the status of embedding for a dataset
    """
    mongo_client = get_mongo_client()
    embedding_status = mongo_client.exempla.embedding_status

    status_record = embedding_status.find_one({"dataset_id": dataset_id})

    if not status_record:
        return {
            "dataset_id": dataset_id,
            "status": "not_found",
            "message": "No embedding process found for this dataset",
        }

    if "_id" in status_record:
        del status_record["_id"]

    return status_record
