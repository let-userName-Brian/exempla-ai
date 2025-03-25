from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from services.config import Config
from services.task_manager import task_manager

cfg = Config()
qdrant = QdrantClient(url=cfg.QDRANT_URL, api_key=cfg.QDRANT_API_KEY)


def upsert_vector(doc_id: str, vector: List[float], metadata: Dict[str, Any]):
    # shutdown check
    if task_manager.should_shutdown():
        raise InterruptedError("Vector store operation interrupted by server shutdown")

    qdrant.upsert(
        collection_name="dataset_vectors",
        points=[models.PointStruct(id=doc_id, vector=vector, payload=metadata)],
    )


def batch_upsert_vectors(
    doc_ids: List[str], vectors: List[List[float]], metadata_list: List[Dict[str, Any]]
):
    # shutdown check
    if task_manager.should_shutdown():
        raise InterruptedError("Vector store operation interrupted by server shutdown")

    if not (len(doc_ids) == len(vectors) == len(metadata_list)):
        raise ValueError(
            "doc_ids, vectors, and metadata_list must have the same length"
        )

    # points for batch upsert
    points = []
    for i in range(len(doc_ids)):
        try:
            point_id = str(doc_ids[i])
            point = models.PointStruct(
                id=point_id, vector=vectors[i], payload=metadata_list[i]
            )
            points.append(point)
        except Exception as e:
            print(f"Error creating point for document {doc_ids[i]}: {str(e)}")

    if not points:
        return

    batch_size = 100
    for i in range(0, len(points), batch_size):
        # shutdown check
        if task_manager.should_shutdown():
            raise InterruptedError(
                "Vector store operation interrupted by server shutdown"
            )

        batch = points[i : i + batch_size]
        try:
            qdrant.upsert(collection_name="dataset_vectors", points=batch)
        except Exception as e:
            print(f"Error upserting batch to Qdrant: {str(e)}")


def search_vectors(query_vector, dataset_id, top_k=5):
    try:
        search_results = qdrant.search(
            collection_name="dataset_vectors",
            query_vector=query_vector,
            query_filter={
                "must": [{"key": "dataset_id", "match": {"value": dataset_id}}]
            },
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        processed_results = []
        for result in search_results:
            payload = result.payload
            metadata = {}
            for key, value in payload.items():
                if key != "content":
                    metadata[key] = value

            processed_doc = {
                "score": result.score,
                "content": payload.get("content", ""),
                "metadata": metadata,
            }
            processed_results.append(processed_doc)

        return processed_results
    except Exception as e:
        print(f"Error searching vectors: {str(e)}")
        return []
