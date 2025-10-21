"""
Sentiment analysis processor for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class SentimentAnalyzer(BaseNLPProcessor):
    """Analyzes sentiment of text using transformer models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("sentiment", config)
        self.model_name = config.get("model_name", "cardiffnlp/twitter-roberta-base-sentiment-latest")
        self.max_length = config.get("max_length", 512)
        self.batch_size = config.get("batch_size", 16)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.sentiment_pipeline = None
        self.tokenizer = None
        self.model = None
    
    async def initialize(self):
        """Initialize the sentiment analyzer"""
        try:
            # Initialize sentiment analysis pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
                max_length=self.max_length,
                truncation=True
            )
            
            # Also initialize tokenizer and model for custom analysis
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.is_initialized = True
            logger.info(f"Sentiment analyzer initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {str(e)}")
            raise
    
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """Analyze sentiment of a single text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    {"sentiment": "neutral", "score": 0.0},
                    confidence=0.0,
                    metadata={"reason": "empty_text"}
                )
            
            # Analyze sentiment
            sentiment_result = await self._analyze_sentiment(processed_text)
            
            return self._create_result(
                ProcessingStatus.COMPLETED,
                sentiment_result,
                confidence=sentiment_result.get("confidence", 0.8),
                metadata={
                    "text_length": len(processed_text),
                    "model_name": self.model_name
                }
            )
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            )
    
    async def process_batch(self, texts: List[str], **kwargs) -> List[ProcessingResult]:
        """Analyze sentiment of multiple texts"""
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
                    {"sentiment": "neutral", "score": 0.0},
                    confidence=0.0,
                    metadata={"reason": "empty_text"}
                ) for _ in texts]
            
            # Analyze sentiment for valid texts
            sentiment_results = await self._analyze_sentiment_batch(valid_texts)
            
            # Create results
            results = []
            result_idx = 0
            
            for i, text in enumerate(texts):
                if i in valid_indices:
                    sentiment_result = sentiment_results[result_idx]
                    result_idx += 1
                    
                    result = self._create_result(
                        ProcessingStatus.COMPLETED,
                        sentiment_result,
                        confidence=sentiment_result.get("confidence", 0.8),
                        metadata={
                            "text_length": len(text),
                            "model_name": self.model_name
                        }
                    )
                else:
                    result = self._create_result(
                        ProcessingStatus.COMPLETED,
                        {"sentiment": "neutral", "score": 0.0},
                        confidence=0.0,
                        metadata={"reason": "empty_text"}
                    )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed: {str(e)}")
            return [self._create_result(
                ProcessingStatus.FAILED,
                None,
                error=str(e)
            ) for _ in texts]
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a single text"""
        try:
            # Use pipeline for sentiment analysis
            result = self.sentiment_pipeline(text)
            
            # Extract sentiment and score
            sentiment = result[0]["label"].lower()
            score = result[0]["score"]
            
            # Normalize sentiment labels
            normalized_sentiment = self._normalize_sentiment_label(sentiment)
            
            # Calculate confidence
            confidence = self._calculate_sentiment_confidence(score, text)
            
            return {
                "sentiment": normalized_sentiment,
                "score": float(score),
                "confidence": confidence,
                "raw_result": result[0]
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _analyze_sentiment_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for a batch of texts"""
        try:
            # Use pipeline for batch sentiment analysis
            results = self.sentiment_pipeline(texts)
            
            sentiment_results = []
            for i, result in enumerate(results):
                sentiment = result["label"].lower()
                score = result["score"]
                
                normalized_sentiment = self._normalize_sentiment_label(sentiment)
                confidence = self._calculate_sentiment_confidence(score, texts[i])
                
                sentiment_results.append({
                    "sentiment": normalized_sentiment,
                    "score": float(score),
                    "confidence": confidence,
                    "raw_result": result
                })
            
            return sentiment_results
            
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed: {str(e)}")
            return [{
                "sentiment": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "error": str(e)
            } for _ in texts]
    
    def _normalize_sentiment_label(self, sentiment: str) -> str:
        """Normalize sentiment labels to standard format"""
        sentiment_lower = sentiment.lower()
        
        # Map various sentiment labels to standard ones
        if sentiment_lower in ["positive", "pos", "good", "favorable"]:
            return "positive"
        elif sentiment_lower in ["negative", "neg", "bad", "unfavorable"]:
            return "negative"
        elif sentiment_lower in ["neutral", "neu", "neutral"]:
            return "neutral"
        else:
            # Default to neutral for unknown labels
            return "neutral"
    
    def _calculate_sentiment_confidence(self, score: float, text: str) -> float:
        """Calculate confidence for sentiment analysis"""
        # Base confidence from model score
        base_confidence = float(score)
        
        # Adjust based on text characteristics
        text_length = len(text)
        word_count = len(text.split())
        
        # Longer texts tend to have more reliable sentiment
        if text_length > 100:
            base_confidence += 0.1
        elif text_length < 20:
            base_confidence -= 0.1
        
        # More words generally mean more reliable sentiment
        if word_count > 10:
            base_confidence += 0.05
        elif word_count < 3:
            base_confidence -= 0.1
        
        # Check for sentiment indicators
        positive_words = ["good", "great", "excellent", "wonderful", "amazing"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disaster"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > 0 or negative_count > 0:
            base_confidence += 0.05
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def get_sentiment_distribution(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get distribution of sentiment results"""
        if not sentiment_results:
            return {"positive": 0, "negative": 0, "neutral": 0}
        
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        total_score = 0.0
        
        for result in sentiment_results:
            sentiment = result.get("sentiment", "neutral")
            score = result.get("score", 0.0)
            
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            
            total_score += score
        
        # Calculate percentages
        total_count = len(sentiment_results)
        percentages = {
            sentiment: (count / total_count) * 100
            for sentiment, count in sentiment_counts.items()
        }
        
        # Calculate average score
        average_score = total_score / total_count if total_count > 0 else 0.0
        
        return {
            "counts": sentiment_counts,
            "percentages": percentages,
            "average_score": average_score,
            "total_count": total_count
        }
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence for sentiment analysis result"""
        if not result_data or "confidence" not in result_data:
            return 0.0
        
        return result_data["confidence"]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the sentiment model"""
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "device": self.device,
            "is_initialized": self.is_initialized
        }
