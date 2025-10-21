"""
NLP processing pipeline for Peace Map platform
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus
from .deduplicator import EventDeduplicator
from .classifier import EventClassifier
from .geocoder import Geocoder
from .embedder import TextEmbedder
from .sentiment import SentimentAnalyzer
from ..ingestion.base import Event

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for NLP pipeline"""
    enable_deduplication: bool = True
    enable_classification: bool = True
    enable_geocoding: bool = True
    enable_embedding: bool = True
    enable_sentiment: bool = True
    parallel_processing: bool = True
    max_batch_size: int = 100


class NLPPipeline:
    """Orchestrates NLP processing pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pipeline_config = PipelineConfig(**config.get("pipeline", {}))
        
        # Initialize processors
        self.deduplicator = None
        self.classifier = None
        self.geocoder = None
        self.embedder = None
        self.sentiment_analyzer = None
        
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize all NLP processors"""
        processor_configs = self.config.get("processors", {})
        
        # Initialize deduplicator
        if self.pipeline_config.enable_deduplication:
            dedup_config = processor_configs.get("deduplicator", {})
            self.deduplicator = EventDeduplicator(dedup_config)
        
        # Initialize classifier
        if self.pipeline_config.enable_classification:
            classifier_config = processor_configs.get("classifier", {})
            self.classifier = EventClassifier(classifier_config)
        
        # Initialize geocoder
        if self.pipeline_config.enable_geocoding:
            geocoder_config = processor_configs.get("geocoder", {})
            self.geocoder = Geocoder(geocoder_config)
        
        # Initialize embedder
        if self.pipeline_config.enable_embedding:
            embedder_config = processor_configs.get("embedder", {})
            self.embedder = TextEmbedder(embedder_config)
        
        # Initialize sentiment analyzer
        if self.pipeline_config.enable_sentiment:
            sentiment_config = processor_configs.get("sentiment", {})
            self.sentiment_analyzer = SentimentAnalyzer(sentiment_config)
    
    async def initialize(self):
        """Initialize all processors"""
        initialization_tasks = []
        
        if self.deduplicator:
            initialization_tasks.append(self.deduplicator.initialize())
        if self.classifier:
            initialization_tasks.append(self.classifier.initialize())
        if self.geocoder:
            initialization_tasks.append(self.geocoder.initialize())
        if self.embedder:
            initialization_tasks.append(self.embedder.initialize())
        if self.sentiment_analyzer:
            initialization_tasks.append(self.sentiment_analyzer.initialize())
        
        if initialization_tasks:
            await asyncio.gather(*initialization_tasks)
            logger.info("NLP pipeline initialized")
    
    async def process_events(self, events: List[Event]) -> List[Event]:
        """Process a list of events through the NLP pipeline"""
        if not events:
            return []
        
        logger.info(f"Processing {len(events)} events through NLP pipeline")
        
        # Step 1: Deduplication
        if self.deduplicator and self.pipeline_config.enable_deduplication:
            logger.info("Running deduplication...")
            dedup_results = await self.deduplicator.process_batch(events)
            if dedup_results and dedup_results[0].data:
                events = dedup_results[0].data["unique_events"]
                logger.info(f"Deduplication complete: {len(events)} unique events")
        
        # Step 2: Classification
        if self.classifier and self.pipeline_config.enable_classification:
            logger.info("Running classification...")
            await self._process_classification(events)
        
        # Step 3: Geocoding
        if self.geocoder and self.pipeline_config.enable_geocoding:
            logger.info("Running geocoding...")
            await self._process_geocoding(events)
        
        # Step 4: Embedding
        if self.embedder and self.pipeline_config.enable_embedding:
            logger.info("Running embedding generation...")
            await self._process_embedding(events)
        
        # Step 5: Sentiment Analysis
        if self.sentiment_analyzer and self.pipeline_config.enable_sentiment:
            logger.info("Running sentiment analysis...")
            await self._process_sentiment(events)
        
        logger.info("NLP pipeline processing complete")
        return events
    
    async def _process_classification(self, events: List[Event]):
        """Process event classification"""
        if not self.classifier:
            return
        
        # Extract texts for classification
        texts = [f"{event.title} {event.description}" for event in events]
        
        # Process in batches
        batch_size = self.pipeline_config.max_batch_size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_events = events[i:i + batch_size]
            
            # Classify batch
            results = await self.classifier.process_batch(batch_texts)
            
            # Update events with classification results
            for j, result in enumerate(results):
                if result.status == ProcessingStatus.COMPLETED and result.data:
                    batch_events[j].category = result.data
                    batch_events[j].confidence = result.confidence
    
    async def _process_geocoding(self, events: List[Event]):
        """Process event geocoding"""
        if not self.geocoder:
            return
        
        # Extract location texts
        location_texts = []
        location_indices = []
        
        for i, event in enumerate(events):
            if event.location and event.location.get("country"):
                # Use existing location info
                continue
            elif event.location and event.location.get("name"):
                location_texts.append(event.location["name"])
                location_indices.append(i)
            else:
                # Try to extract location from title/description
                text = f"{event.title} {event.description}"
                location_texts.append(text)
                location_indices.append(i)
        
        if not location_texts:
            return
        
        # Process in batches
        batch_size = self.pipeline_config.max_batch_size
        for i in range(0, len(location_texts), batch_size):
            batch_texts = location_texts[i:i + batch_size]
            batch_indices = location_indices[i:i + batch_size]
            
            # Geocode batch
            results = await self.geocoder.process_batch(batch_texts)
            
            # Update events with geocoding results
            for j, result in enumerate(results):
                if result.status == ProcessingStatus.COMPLETED and result.data:
                    event_index = batch_indices[j]
                    events[event_index].location = result.data
    
    async def _process_embedding(self, events: List[Event]):
        """Process event embedding generation"""
        if not self.embedder:
            return
        
        # Extract texts for embedding
        texts = [f"{event.title} {event.description}" for event in events]
        
        # Process in batches
        batch_size = self.pipeline_config.max_batch_size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_events = events[i:i + batch_size]
            
            # Generate embeddings
            results = await self.embedder.process_batch(batch_texts)
            
            # Update events with embeddings
            for j, result in enumerate(results):
                if result.status == ProcessingStatus.COMPLETED and result.data:
                    batch_events[j].embedding = result.data
    
    async def _process_sentiment(self, events: List[Event]):
        """Process event sentiment analysis"""
        if not self.sentiment_analyzer:
            return
        
        # Extract texts for sentiment analysis
        texts = [f"{event.title} {event.description}" for event in events]
        
        # Process in batches
        batch_size = self.pipeline_config.max_batch_size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_events = events[i:i + batch_size]
            
            # Analyze sentiment
            results = await self.sentiment_analyzer.process_batch(batch_texts)
            
            # Update events with sentiment results
            for j, result in enumerate(results):
                if result.status == ProcessingStatus.COMPLETED and result.data:
                    batch_events[j].sentiment_score = result.data.get("score", 0.0)
    
    async def process_single_event(self, event: Event) -> Event:
        """Process a single event through the pipeline"""
        return (await self.process_events([event]))[0]
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of all processors in the pipeline"""
        status = {
            "pipeline_config": {
                "deduplication": self.pipeline_config.enable_deduplication,
                "classification": self.pipeline_config.enable_classification,
                "geocoding": self.pipeline_config.enable_geocoding,
                "embedding": self.pipeline_config.enable_embedding,
                "sentiment": self.pipeline_config.enable_sentiment,
                "parallel_processing": self.pipeline_config.parallel_processing
            },
            "processors": {}
        }
        
        if self.deduplicator:
            status["processors"]["deduplicator"] = self.deduplicator.get_status()
        if self.classifier:
            status["processors"]["classifier"] = self.classifier.get_status()
        if self.geocoder:
            status["processors"]["geocoder"] = self.geocoder.get_status()
        if self.embedder:
            status["processors"]["embedder"] = self.embedder.get_status()
        if self.sentiment_analyzer:
            status["processors"]["sentiment"] = self.sentiment_analyzer.get_status()
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all processors"""
        health_status = {
            "overall_health": "healthy",
            "processors": {},
            "last_check": datetime.utcnow().isoformat()
        }
        
        processors = [
            ("deduplicator", self.deduplicator),
            ("classifier", self.classifier),
            ("geocoder", self.geocoder),
            ("embedder", self.embedder),
            ("sentiment", self.sentiment_analyzer)
        ]
        
        for name, processor in processors:
            if processor:
                try:
                    status = processor.get_status()
                    health_status["processors"][name] = {
                        "status": "healthy",
                        "initialized": status.get("initialized", False)
                    }
                except Exception as e:
                    health_status["processors"][name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["overall_health"] = "degraded"
            else:
                health_status["processors"][name] = {
                    "status": "disabled"
                }
        
        return health_status
    
    async def close(self):
        """Close all processors and cleanup resources"""
        if self.geocoder and hasattr(self.geocoder, 'close'):
            await self.geocoder.close()
        
        logger.info("NLP pipeline closed")
