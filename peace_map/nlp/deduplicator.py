"""
Event deduplication processor for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus
from ..ingestion.base import Event

logger = logging.getLogger(__name__)


class EventDeduplicator(BaseNLPProcessor):
    """Deduplicates events based on content similarity and temporal proximity"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("deduplicator", config)
        self.similarity_threshold = config.get("similarity_threshold", 0.8)
        self.temporal_window_hours = config.get("temporal_window_hours", 24)
        self.min_text_length = config.get("min_text_length", 10)
        self.embedding_model = None
    
    async def initialize(self):
        """Initialize the deduplicator"""
        try:
            # Initialize embedding model for similarity calculation
            from sentence_transformers import SentenceTransformer
            model_name = self.config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            self.is_initialized = True
            logger.info("Event deduplicator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize deduplicator: {str(e)}")
            raise
    
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """Process single text for deduplication (not used directly)"""
        return self._create_result(
            ProcessingStatus.COMPLETED,
            {"text": text, "embedding": None},
            metadata={"note": "Use process_batch for deduplication"}
        )
    
    async def process_batch(self, events: List[Event], **kwargs) -> List[ProcessingResult]:
        """Deduplicate a batch of events"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Filter events by minimum text length
            valid_events = [e for e in events if len(e.title + " " + e.description) >= self.min_text_length]
            
            if len(valid_events) < 2:
                return [self._create_result(ProcessingStatus.COMPLETED, {"unique_events": valid_events})]
            
            # Generate embeddings for all events
            texts = [f"{event.title} {event.description}" for event in valid_events]
            embeddings = self.embedding_model.encode(texts)
            
            # Find duplicate groups
            duplicate_groups = self._find_duplicate_groups(valid_events, embeddings)
            
            # Create deduplicated events
            unique_events = self._create_unique_events(valid_events, duplicate_groups)
            
            return [self._create_result(
                ProcessingStatus.COMPLETED,
                {"unique_events": unique_events, "duplicate_groups": duplicate_groups},
                confidence=0.9,
                metadata={
                    "original_count": len(valid_events),
                    "unique_count": len(unique_events),
                    "duplicates_removed": len(valid_events) - len(unique_events)
                }
            )]
            
        except Exception as e:
            logger.error(f"Deduplication failed: {str(e)}")
            return [self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            )]
    
    def _find_duplicate_groups(self, events: List[Event], embeddings: np.ndarray) -> List[List[int]]:
        """Find groups of duplicate events"""
        duplicate_groups = []
        processed = set()
        
        for i, event in enumerate(events):
            if i in processed:
                continue
            
            # Find events within temporal window
            temporal_candidates = self._find_temporal_candidates(events, event, i)
            
            if not temporal_candidates:
                continue
            
            # Calculate similarities with temporal candidates
            similarities = self._calculate_similarities(embeddings, i, temporal_candidates)
            
            # Find similar events
            similar_indices = [j for j, sim in zip(temporal_candidates, similarities) if sim >= self.similarity_threshold]
            
            if similar_indices:
                # Create duplicate group
                group = [i] + similar_indices
                duplicate_groups.append(group)
                processed.update(group)
        
        return duplicate_groups
    
    def _find_temporal_candidates(self, events: List[Event], target_event: Event, target_index: int) -> List[int]:
        """Find events within temporal window of target event"""
        candidates = []
        target_time = target_event.published_at
        
        for i, event in enumerate(events):
            if i == target_index:
                continue
            
            time_diff = abs((event.published_at - target_time).total_seconds())
            if time_diff <= self.temporal_window_hours * 3600:
                candidates.append(i)
        
        return candidates
    
    def _calculate_similarities(self, embeddings: np.ndarray, target_index: int, candidate_indices: List[int]) -> List[float]:
        """Calculate cosine similarities between target and candidate embeddings"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        target_embedding = embeddings[target_index].reshape(1, -1)
        candidate_embeddings = embeddings[candidate_indices]
        
        similarities = cosine_similarity(target_embedding, candidate_embeddings)[0]
        return similarities.tolist()
    
    def _create_unique_events(self, events: List[Event], duplicate_groups: List[List[int]]) -> List[Event]:
        """Create unique events by merging duplicates"""
        unique_events = []
        processed = set()
        
        for i, event in enumerate(events):
            if i in processed:
                continue
            
            # Check if this event is part of a duplicate group
            group = None
            for group_indices in duplicate_groups:
                if i in group_indices:
                    group = group_indices
                    break
            
            if group:
                # Merge duplicate events
                merged_event = self._merge_duplicate_events([events[j] for j in group])
                unique_events.append(merged_event)
                processed.update(group)
            else:
                # Keep original event
                unique_events.append(event)
                processed.add(i)
        
        return unique_events
    
    def _merge_duplicate_events(self, duplicate_events: List[Event]) -> Event:
        """Merge duplicate events into a single event"""
        if not duplicate_events:
            return None
        
        if len(duplicate_events) == 1:
            return duplicate_events[0]
        
        # Use the event with highest confidence as base
        base_event = max(duplicate_events, key=lambda e: e.confidence)
        
        # Merge information from all events
        merged_title = base_event.title
        merged_description = base_event.description
        
        # Combine descriptions if they're different
        descriptions = [e.description for e in duplicate_events if e.description and e.description != merged_description]
        if descriptions:
            merged_description += " " + " ".join(descriptions)
        
        # Combine sources
        sources = list(set([e.source for e in duplicate_events]))
        merged_source = ", ".join(sources)
        
        # Combine tags
        all_tags = []
        for event in duplicate_events:
            all_tags.extend(event.tags)
        merged_tags = list(set(all_tags))
        
        # Use earliest publication date
        earliest_date = min(e.published_at for e in duplicate_events)
        
        # Use highest confidence
        max_confidence = max(e.confidence for e in duplicate_events)
        
        # Combine raw data
        merged_raw_data = {
            "merged_from": [e.id for e in duplicate_events],
            "original_events": [e.raw_data for e in duplicate_events],
            "merge_timestamp": datetime.utcnow().isoformat()
        }
        
        # Create merged event
        merged_event = Event(
            id=f"merged_{base_event.id}",
            title=merged_title,
            description=merged_description,
            source=merged_source,
            source_url=base_event.source_url,
            published_at=earliest_date,
            location=base_event.location,
            category=base_event.category,
            severity=base_event.severity,
            confidence=max_confidence,
            raw_data=merged_raw_data,
            tags=merged_tags
        )
        
        return merged_event
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence for deduplication result"""
        if not result_data or "unique_events" not in result_data:
            return 0.0
        
        original_count = metadata.get("original_count", 0)
        unique_count = metadata.get("unique_count", 0)
        
        if original_count == 0:
            return 0.0
        
        # Higher confidence if more duplicates were found
        duplicate_ratio = (original_count - unique_count) / original_count
        return min(0.5 + duplicate_ratio, 1.0)
