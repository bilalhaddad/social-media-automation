"""
NLP processing module for Peace Map platform
"""

from .base import BaseNLPProcessor
from .deduplicator import EventDeduplicator
from .classifier import EventClassifier
from .geocoder import Geocoder
from .embedder import TextEmbedder
from .sentiment import SentimentAnalyzer
from .pipeline import NLPPipeline

__all__ = [
    "BaseNLPProcessor",
    "EventDeduplicator",
    "EventClassifier", 
    "Geocoder",
    "TextEmbedder",
    "SentimentAnalyzer",
    "NLPPipeline"
]
