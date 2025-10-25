import faiss
import numpy as np
import pickle
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Search:
    def __init__(self):
        # Initialize Gemini for embeddings
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.embedding_model = "models/embedding-001"  # Gemini's embedding model
        else:
            print("Warning: GEMINI_API_KEY not found, search functionality disabled")
            self.embedding_model = None

        try:
            self.index = faiss.read_index('models/faiss_index/index.faiss')
            with open('models/faiss_index/metadata.pkl', 'rb') as f:
                self.metadata = pickle.load(f)
        except (FileNotFoundError, IOError, Exception):
            self.index = None
            self.metadata = []

    async def query(self, text):
        if not self.index or not self.embedding_model:
            return ''

        try:
            # Use Gemini for embeddings
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"  # Optimized for retrieval
            )
            query_emb = np.array(result['embedding'], dtype=np.float32).reshape(1, -1)

            # Normalize for cosine similarity
            faiss.normalize_L2(query_emb)

            # Search - get more results for better context
            distances, indices = self.index.search(query_emb, 5)  # Increased from 3 to 5

            # Filter by distance threshold (cosine similarity > 0.7)
            relevant_indices = []
            for i, distance in enumerate(distances[0]):
                if distance > 0.7:  # Cosine similarity threshold
                    relevant_indices.append(indices[0][i])

            if not relevant_indices:
                return ''

            paragraphs = [self.metadata[i] for i in relevant_indices[:3]]  # Limit to top 3
            context = ' '.join(paragraphs)

            # Increased context limit for Gemini's larger context window (2M tokens)
            max_context_length = 4000  # Increased from 1000
            if len(context) > max_context_length:
                context = context[:max_context_length] + "..."

            return context

        except Exception as e:
            print(f"Search error: {e}")
            return ''
