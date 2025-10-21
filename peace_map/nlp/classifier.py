"""
Event classification processor for Peace Map platform
"""

import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

from .base import BaseNLPProcessor, ProcessingResult, ProcessingStatus
from ..ingestion.base import EventCategory

logger = logging.getLogger(__name__)


class EventClassifier(BaseNLPProcessor):
    """Classifies events into categories using ML models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("classifier", config)
        self.model_path = config.get("model_path", "models/event_classifier.joblib")
        self.retrain_threshold = config.get("retrain_threshold", 100)
        self.categories = [
            EventCategory.PROTEST,
            EventCategory.CYBER,
            EventCategory.KINETIC,
            EventCategory.ECONOMIC,
            EventCategory.ENVIRONMENTAL,
            EventCategory.POLITICAL
        ]
        self.classifier = None
        self.vectorizer = None
        self.training_data = []
    
    async def initialize(self):
        """Initialize the classifier"""
        try:
            # Try to load existing model
            if os.path.exists(self.model_path):
                self._load_model()
                logger.info("Event classifier model loaded")
            else:
                # Initialize with default model
                self._initialize_default_model()
                logger.info("Event classifier initialized with default model")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize classifier: {str(e)}")
            raise
    
    def _load_model(self):
        """Load pre-trained model from file"""
        try:
            model_data = joblib.load(self.model_path)
            self.classifier = model_data['classifier']
            self.vectorizer = model_data['vectorizer']
            logger.info("Classifier model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self._initialize_default_model()
    
    def _initialize_default_model(self):
        """Initialize with a simple default model"""
        # Create a simple pipeline with TF-IDF and Logistic Regression
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        self.classifier = LogisticRegression(
            random_state=42,
            max_iter=1000
        )
        
        # Train with some basic examples
        self._train_with_examples()
    
    def _train_with_examples(self):
        """Train with basic examples"""
        examples = [
            ("protest demonstration rally strike", EventCategory.PROTEST),
            ("cyber attack hack breach malware", EventCategory.CYBER),
            ("attack violence conflict bomb", EventCategory.KINETIC),
            ("economic financial market trade", EventCategory.ECONOMIC),
            ("environment climate disaster flood", EventCategory.ENVIRONMENTAL),
            ("political election government policy", EventCategory.POLITICAL),
        ]
        
        texts = [ex[0] for ex in examples]
        labels = [ex[1].value for ex in examples]
        
        # Fit vectorizer and classifier
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
    
    async def process(self, text: str, **kwargs) -> ProcessingResult:
        """Classify a single text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            if not processed_text:
                return self._create_result(
                    ProcessingStatus.COMPLETED,
                    EventCategory.UNKNOWN,
                    confidence=0.0,
                    metadata={"reason": "empty_text"}
                )
            
            # Classify
            category, confidence = self._classify_text(processed_text)
            
            return self._create_result(
                ProcessingStatus.COMPLETED,
                category,
                confidence=confidence,
                metadata={"text_length": len(processed_text)}
            )
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return self._create_result(
                ProcessingStatus.FAILED,
                EventCategory.UNKNOWN,
                error=str(e)
            )
    
    async def process_batch(self, texts: List[str], **kwargs) -> List[ProcessingResult]:
        """Classify multiple texts"""
        if not self.is_initialized:
            await self.initialize()
        
        results = []
        
        for text in texts:
            result = await self.process(text)
            results.append(result)
        
        return results
    
    def _classify_text(self, text: str) -> Tuple[EventCategory, float]:
        """Classify text and return category with confidence"""
        try:
            # Vectorize text
            X = self.vectorizer.transform([text])
            
            # Get prediction probabilities
            probabilities = self.classifier.predict_proba(X)[0]
            predicted_class = self.classifier.predict(X)[0]
            
            # Get confidence (max probability)
            confidence = float(max(probabilities))
            
            # Convert to EventCategory
            try:
                category = EventCategory(predicted_class)
            except ValueError:
                category = EventCategory.UNKNOWN
            
            return category, confidence
            
        except Exception as e:
            logger.error(f"Classification error: {str(e)}")
            return EventCategory.UNKNOWN, 0.0
    
    def add_training_data(self, text: str, category: EventCategory):
        """Add training data for retraining"""
        self.training_data.append((text, category))
        
        # Check if we should retrain
        if len(self.training_data) >= self.retrain_threshold:
            self._retrain_model()
    
    def _retrain_model(self):
        """Retrain the model with accumulated data"""
        if len(self.training_data) < 10:  # Need minimum data
            return
        
        try:
            # Prepare training data
            texts = [item[0] for item in self.training_data]
            labels = [item[1].value for item in self.training_data]
            
            # Retrain
            X = self.vectorizer.fit_transform(texts)
            self.classifier.fit(X, labels)
            
            # Save model
            self._save_model()
            
            # Clear training data
            self.training_data = []
            
            logger.info(f"Model retrained with {len(texts)} examples")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}")
    
    def _save_model(self):
        """Save the trained model"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            model_data = {
                'classifier': self.classifier,
                'vectorizer': self.vectorizer,
                'categories': [cat.value for cat in self.categories]
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
    
    def get_classification_features(self, text: str) -> Dict[str, Any]:
        """Get features used for classification"""
        if not self.is_initialized:
            return {}
        
        try:
            # Get TF-IDF features
            X = self.vectorizer.transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            feature_scores = X.toarray()[0]
            
            # Get top features
            top_indices = np.argsort(feature_scores)[-10:][::-1]
            top_features = {
                feature_names[i]: float(feature_scores[i])
                for i in top_indices if feature_scores[i] > 0
            }
            
            return {
                "top_features": top_features,
                "text_length": len(text),
                "word_count": len(text.split()),
                "has_numbers": any(char.isdigit() for char in text),
                "has_capitals": any(char.isupper() for char in text)
            }
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return {}
    
    def _calculate_confidence(self, result_data: Any, metadata: Dict[str, Any]) -> float:
        """Calculate confidence for classification result"""
        if isinstance(result_data, EventCategory):
            # Confidence is already calculated in _classify_text
            return metadata.get("confidence", 0.5)
        return 0.0
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_path": self.model_path,
            "categories": [cat.value for cat in self.categories],
            "training_data_count": len(self.training_data),
            "retrain_threshold": self.retrain_threshold,
            "is_initialized": self.is_initialized
        }
