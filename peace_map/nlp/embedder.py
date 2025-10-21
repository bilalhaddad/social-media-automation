"""
Text embedding processor for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from sentence_transformers import SentenceTransformer
import torch

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class TextEmbedder(BaseNLPProcessor):
    """Generates text embeddings for similarity and clustering"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("embedder", config)
        self.model_name = config.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
        self.max_length = config.get("max_length", 512)
        self.batch_size = config.get("batch_size", 32)
        self.normalize_embeddings = config.get("normalize_embeddings", True)
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def initialize(self):
        """Initialize the embedding model"""
        try:
            # Load the sentence transformer model
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Set model to evaluation mode
            self.model.eval()
            
            self.is_initialized = True
            logger.info(f"Text embedder initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedder: {str(e)}")
            raise
    
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """Generate embedding for a single text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    None,
                    confidence=0.0,
                    metadata={"reason": "empty_text"}
                )
            
            # Generate embedding
            embedding = await self._generate_embedding(processed_text)
            
            if embedding is not None:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    embedding,
                    confidence=0.9,
                    metadata={
                        "text_length": len(processed_text),
                        "embedding_dimension": len(embedding),
                        "model_name": self.model_name
                    }
                )
            else:
                return self._create_result(
                    ProcessingStatus.FAILED,
                    None,
                    error="Embedding generation failed"
                )
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            )
    
    async def process_batch(self, texts: List[str], **kwargs) -> List[ProcessingResult]:
        """Generate embeddings for multiple texts"""
        if not self.is_initialized:
            await self.initialize()
        
        results = []
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_results = await self._process_batch(batch_texts)
            results.extend(batch_results)
        
        return results
    
    async def _process_batch(self, texts: List[str]) -> List[ProcessingResult]:
        """Process a batch of texts"""
        try:
            # Preprocess texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Filter out empty texts
            valid_texts = [text for text in processed_texts if text]
            valid_indices = [i for i, text in enumerate(processed_texts) if text]
            
            if not valid_texts:
                return [self._create_result(
                    ProcessingStatus.COMPLETED,
                    None,
                    confidence=0.0,
                    metadata={"reason": "empty_text"}
                ) for _ in texts]
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_batch(valid_texts)
            
            # Create results
            results = []
            embedding_idx = 0
            
            for i, text in enumerate(texts):
                if i in valid_indices:
                    embedding = embeddings[embedding_idx]
                    embedding_idx += 1
                    
                    result = self._create_result(
                        ProcessingStatus.COMPLETED,
                        embedding,
                        confidence=0.9,
                        metadata={
                            "text_length": len(text),
                            "embedding_dimension": len(embedding),
                            "model_name": self.model_name
                        }
                    )
                else:
                    result = self._create_result(
                        ProcessingStatus.COMPLETED,
                        None,
                        confidence=0.0,
                        metadata={"reason": "empty_text"}
                    )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            return [self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            ) for _ in texts]
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        try:
            # Encode text to embedding
            embedding = self.model.encode(
                text,
                convert_to_tensor=False,
                normalize_embeddings=self.normalize_embeddings
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Single embedding generation failed: {str(e)}")
            return None
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            # Encode texts to embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                normalize_embeddings=self.normalize_embeddings,
                batch_size=self.batch_size
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            return []
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], candidate_embeddings: List[List[float]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query"""
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            return []
    
    def cluster_embeddings(self, embeddings: List[List[float]], n_clusters: int = None) -> Dict[str, Any]:
        """Cluster embeddings using K-means"""
        try:
            from sklearn.cluster import KMeans
            
            if not embeddings:
                return {"clusters": [], "labels": []}
            
            # Determine number of clusters
            if n_clusters is None:
                n_clusters = min(len(embeddings) // 2, 10)
            
            if n_clusters <= 0:
                return {"clusters": [0] * len(embeddings), "labels": [0] * len(embeddings)}
            
            # Perform clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(embeddings)
            
            return {
                "clusters": labels.tolist(),
                "labels": labels.tolist(),
                "centers": kmeans.cluster_centers_.tolist(),
                "n_clusters": n_clusters
            }
            
        except Exception as e:
            logger.error(f"Clustering failed: {str(e)}")
            return {"clusters": [], "labels": []}
    
    def reduce_dimensions(self, embeddings: List[List[float]], n_components: int = 2) -> List[List[float]]:
        """Reduce embedding dimensions using PCA"""
        try:
            from sklearn.decomposition import PCA
            
            if not embeddings:
                return []
            
            # Perform PCA
            pca = PCA(n_components=n_components)
            reduced_embeddings = pca.fit_transform(embeddings)
            
            return reduced_embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Dimension reduction failed: {str(e)}")
            return []
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence for embedding result"""
        if result_data is None:
            return 0.0
        
        # High confidence for successful embedding generation
        return 0.9
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "normalize_embeddings": self.normalize_embeddings,
            "device": self.device,
            "is_initialized": self.is_initialized,
            "embedding_dimension": self.model.get_sentence_embedding_dimension() if self.model else None
        }
