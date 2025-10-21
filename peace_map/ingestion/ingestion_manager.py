"""
Ingestion manager for coordinating data ingestion from multiple sources
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .base import BaseIngestionConnector, Event
from .rss_connector import RSSConnector
from .gdelt_connector import GDELTConnector
from .acled_connector import ACLEDConnector
from .maritime_connector import MaritimeConnector

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics for ingestion process"""
    total_events: int = 0
    successful_connectors: int = 0
    failed_connectors: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class IngestionManager:
    """Manages data ingestion from multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connectors: List[BaseIngestionConnector] = []
        self.stats = IngestionStats()
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize all configured connectors"""
        connector_configs = self.config.get("connectors", {})
        
        # Initialize RSS connector
        if connector_configs.get("rss", {}).get("enabled", False):
            try:
                rss_connector = RSSConnector(connector_configs["rss"])
                if rss_connector.validate_config():
                    self.connectors.append(rss_connector)
                    logger.info("RSS connector initialized")
                else:
                    logger.error("RSS connector configuration invalid")
            except Exception as e:
                logger.error(f"Failed to initialize RSS connector: {str(e)}")
        
        # Initialize GDELT connector
        if connector_configs.get("gdelt", {}).get("enabled", False):
            try:
                gdelt_connector = GDELTConnector(connector_configs["gdelt"])
                if gdelt_connector.validate_config():
                    self.connectors.append(gdelt_connector)
                    logger.info("GDELT connector initialized")
                else:
                    logger.error("GDELT connector configuration invalid")
            except Exception as e:
                logger.error(f"Failed to initialize GDELT connector: {str(e)}")
        
        # Initialize ACLED connector
        if connector_configs.get("acled", {}).get("enabled", False):
            try:
                acled_connector = ACLEDConnector(connector_configs["acled"])
                if acled_connector.validate_config():
                    self.connectors.append(acled_connector)
                    logger.info("ACLED connector initialized")
                else:
                    logger.error("ACLED connector configuration invalid")
            except Exception as e:
                logger.error(f"Failed to initialize ACLED connector: {str(e)}")
        
        # Initialize Maritime connector
        if connector_configs.get("maritime", {}).get("enabled", False):
            try:
                maritime_connector = MaritimeConnector(connector_configs["maritime"])
                if maritime_connector.validate_config():
                    self.connectors.append(maritime_connector)
                    logger.info("Maritime connector initialized")
                else:
                    logger.error("Maritime connector configuration invalid")
            except Exception as e:
                logger.error(f"Failed to initialize Maritime connector: {str(e)}")
        
        logger.info(f"Initialized {len(self.connectors)} connectors")
    
    async def fetch_all_events(self, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from all enabled connectors"""
        start_time = datetime.utcnow()
        all_events = []
        
        logger.info(f"Starting ingestion from {len(self.connectors)} connectors")
        
        # Process connectors in parallel
        tasks = []
        for connector in self.connectors:
            if connector.is_enabled and connector.should_update():
                task = self._fetch_connector_events(connector, since)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Connector {i} failed: {str(result)}")
                    self.stats.failed_connectors += 1
                    self.stats.errors.append(f"Connector {i}: {str(result)}")
                else:
                    all_events.extend(result)
                    self.stats.successful_connectors += 1
        
        # Update statistics
        self.stats.total_events = len(all_events)
        self.stats.processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"Ingestion completed: {self.stats.total_events} events from {self.stats.successful_connectors} connectors")
        
        return all_events
    
    async def _fetch_connector_events(self, connector: BaseIngestionConnector, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from a single connector"""
        try:
            if hasattr(connector, '__aenter__'):
                # Use async context manager for connectors that need it
                async with connector:
                    events = await connector.fetch_events(since)
            else:
                # Direct method call for simple connectors
                events = await connector.fetch_events(since)
            
            logger.info(f"Connector {connector.name} fetched {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Error fetching events from {connector.name}: {str(e)}")
            raise
    
    async def fetch_connector_events(self, connector_name: str, since: Optional[datetime] = None) -> List[Event]:
        """Fetch events from a specific connector"""
        connector = self.get_connector(connector_name)
        if not connector:
            raise ValueError(f"Connector {connector_name} not found")
        
        return await self._fetch_connector_events(connector, since)
    
    def get_connector(self, name: str) -> Optional[BaseIngestionConnector]:
        """Get connector by name"""
        for connector in self.connectors:
            if connector.name == name:
                return connector
        return None
    
    def get_connector_status(self) -> List[Dict[str, Any]]:
        """Get status of all connectors"""
        return [connector.get_status() for connector in self.connectors]
    
    def get_ingestion_stats(self) -> IngestionStats:
        """Get ingestion statistics"""
        return self.stats
    
    def reset_stats(self):
        """Reset ingestion statistics"""
        self.stats = IngestionStats()
    
    async def test_connectors(self) -> Dict[str, bool]:
        """Test all connectors to ensure they're working"""
        results = {}
        
        for connector in self.connectors:
            try:
                if hasattr(connector, '__aenter__'):
                    async with connector:
                        # Try to fetch a small number of recent events
                        events = await connector.fetch_events()
                        results[connector.name] = True
                        logger.info(f"Connector {connector.name} test successful")
                else:
                    events = await connector.fetch_events()
                    results[connector.name] = True
                    logger.info(f"Connector {connector.name} test successful")
            except Exception as e:
                results[connector.name] = False
                logger.error(f"Connector {connector.name} test failed: {str(e)}")
        
        return results
    
    def enable_connector(self, name: str):
        """Enable a specific connector"""
        connector = self.get_connector(name)
        if connector:
            connector.is_enabled = True
            logger.info(f"Connector {name} enabled")
        else:
            logger.error(f"Connector {name} not found")
    
    def disable_connector(self, name: str):
        """Disable a specific connector"""
        connector = self.get_connector(name)
        if connector:
            connector.is_enabled = False
            logger.info(f"Connector {name} disabled")
        else:
            logger.error(f"Connector {name} not found")
    
    def update_connector_config(self, name: str, config: Dict[str, Any]):
        """Update connector configuration"""
        connector = self.get_connector(name)
        if connector:
            connector.config.update(config)
            logger.info(f"Connector {name} configuration updated")
        else:
            logger.error(f"Connector {name} not found")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all connectors"""
        health_status = {
            "overall_health": "healthy",
            "connectors": {},
            "total_connectors": len(self.connectors),
            "enabled_connectors": len([c for c in self.connectors if c.is_enabled]),
            "last_check": datetime.utcnow().isoformat()
        }
        
        for connector in self.connectors:
            try:
                status = connector.get_status()
                health_status["connectors"][connector.name] = {
                    "status": "healthy" if connector.is_enabled else "disabled",
                    "last_update": status.get("last_update"),
                    "should_update": status.get("should_update"),
                    "enabled": connector.is_enabled
                }
            except Exception as e:
                health_status["connectors"][connector.name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "enabled": connector.is_enabled
                }
                health_status["overall_health"] = "degraded"
        
        return health_status
