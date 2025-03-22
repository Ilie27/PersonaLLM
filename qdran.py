import logging
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from sentence_transformers import SentenceTransformer
from config.config import AppConfig

logger = logging.getLogger(__name__)

# Initialize Qdrant Client
qdrant_client = QdrantClient(host=AppConfig.QDRANT_HOST, port=AppConfig.QDRANT_PORT)

# Initialize text embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "source_texts"


def create_collection_if_not_exists():
 """
 Ensures the Qdrant collection exists. If not, creates a new one.
 """
 collections = qdrant_client.get_collections()
 if COLLECTION_NAME not in [col.name for col in collections.collections]:
    logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
    qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )


create_collection_if_not_exists()


def insert_text_chunks(document_id: str, chunks: list):
 """
 Inserts chunked text into Qdrant as embeddings.
 """
 points = []
 for idx, chunk in enumerate(chunks):
    embedding = embedding_model.encode(chunk).tolist()
    point_id = str(uuid.uuid4())

 points.append(PointStruct(id=point_id, vector=embedding, payload={"document_id": document_id, "text": chunk}))

 if points:
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(f"Inserted {len(points)} chunks into Qdrant.")

 return len(points)


def query_similar_texts(text: str, threshold: float, limit: int = 5) -> List[Dict[str, Any]]:
 """
 Queries Qdrant for texts similar to the provided input text.

 Args:
 text (str): The input text to search similar texts for.
 threshold (float): The minimum similarity score (e.g., 0.8) for a point to be considered similar.
 limit (int, optional): Maximum number of results to retrieve. Defaults to 5.

 Returns:
 List[Dict[str, Any]]: A list of candidate dictionaries, each containing:
 - "text": candidate source text (from the payload)
 - "score": semantic similarity score returned by Qdrant.
 """
 # Encode the text into an embedding vector.
 query_vector = embedding_model.encode(text).tolist()

 # Perform the semantic search in Qdrant.
 results = qdrant_client.search(
 collection_name=COLLECTION_NAME,
 query_vector=query_vector,
 limit=limit,
 with_payload=True
 )

 potential_sources = []
 for result in results:
    if result.score >= threshold:
        candidate = {
        "text": result.payload.get("text", ""),
        "score": result.score
        }
 potential_sources.append(candidate)

 logger.info(f"Query returned {len(potential_sources)} potential sources for text: {text[:30]}...")
 return potential_sources

insert_text_chunks("doc1", ["This is a sample text.", "It contains multiple sentences."])