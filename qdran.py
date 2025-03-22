import logging
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from sentence_transformers import SentenceTransformer
from config import AppConfig
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import librosa
import google.generativeai as genai  # Import the Google Gemini library
import os

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

def insert_data_chunks(document_id: str, chunks: list, image_paths: List[str] = None, audio_paths: List[str] = None):
    """
    Inserts chunked text, images, and audio into Qdrant as embeddings.
    """
    points = []

    # Insert text chunks
    for idx, chunk in enumerate(chunks):
        embedding = embedding_model.encode(chunk).tolist()
        point_id = str(uuid.uuid4())
        points.append(PointStruct(id=point_id, vector=embedding, payload={"document_id": document_id, "text": chunk}))

    # Insert image data (if any)
    if image_paths:
        clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        for image_path in image_paths:
            image = Image.open(image_path)
            inputs = clip_processor(images=image, return_tensors="pt", padding=True)
            image_features = clip_model.get_image_features(**inputs).detach().numpy().flatten().tolist()  # Flatten the image features
            point_id = str(uuid.uuid4())
            points.append(PointStruct(id=point_id, vector=image_features, payload={"document_id": document_id, "image_path": image_path}))

    # Insert audio data (if any)
    if audio_paths:
        for audio_path in audio_paths:
            # Using librosa to extract features or a speech-to-text API to transcribe audio into text
            y, sr = librosa.load(audio_path)
            audio_features = librosa.feature.mfcc(y=y, sr=sr).flatten().tolist()  # Example: MFCC features as audio embedding
            point_id = str(uuid.uuid4())
            points.append(PointStruct(id=point_id, vector=audio_features, payload={"document_id": document_id, "audio_path": audio_path}))

    # Upsert the data into Qdrant
    if points:
        qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
        logger.info(f"Inserted {len(points)} chunks (text, images, audio) into Qdrant.")
    
    return len(points)

def query_similar_texts(text: str, threshold: float, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Queries Qdrant for texts similar to the provided input text.
    """
    query_vector = embedding_model.encode(text).tolist()

    # Use `search()` instead of `query_points()`
    results = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        with_payload=True  # Ensures we retrieve the stored texts
    )

    potential_sources = []
    for result in results:
        if result.score >= threshold:
            potential_sources.append({"text": result.payload.get("text", ""), "score": result.score})

    logger.info(f"Query returned {len(potential_sources)} potential sources for text: {text[:30]}...")
    
    if not potential_sources:
        print("No relevant texts found in Qdrant!")
    
    return potential_sources


document_id = "doc_123"

with open("PersonaLLM/data/text/conversation.txt", "r", encoding="utf-8") as file:
    conversation = file.read()

chunks = conversation.split("\n\n")

# audio_paths = ["audio1.wav", "audio2.wav"]

insert_data_chunks(document_id, chunks)

genai.configure(
    api_key=os.environ["GEMINI_API_KEY"]
)  # Ensure you have GEMINI_API_KEY set in your environment variables

# Initialize the Gemini model
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

def get_llm_response_gemini(prompt: str, threshold: float = 0.1, limit: int = 3):
    # First, query similar texts based on the prompt
    similar_texts = query_similar_texts(prompt, threshold=threshold, limit=limit)
    
    # Combine the similar texts into the context
    context = "\n".join([f"Similar text {idx+1}: {entry['text']}" for idx, entry in enumerate(similar_texts)])
    context_text = f"Here are some relevant conversation snippets:\n{context}"
    # Combine the prompt with the context for the Gemini input
    prompt_text = f"Prompt: {prompt}\n\nContext:\n{context_text}\n\nAnswer the following based on the prompt and context."

    try:
        # Generate the response using the Gemini model
        response = gemini_model.generate_content(prompt_text)

        if response and response.text:
            return response.text
        else:
            return None  # Return None if there's no text in the response
    except Exception as e:
        # Log or handle the error if needed
        print(f"Error while querying Gemini: {e}")
        return None

prompt="What drink does Jake drink?"
print(get_llm_response_gemini(prompt, threshold=0.2, limit=3))