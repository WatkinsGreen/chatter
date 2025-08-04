from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
import logging

logger = logging.getLogger(__name__)

class MonitoringConnector(ABC):
    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def get_recent_deployments(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_metric_anomalies(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_error_spikes(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_alerts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        pass
    
    async def health_check(self) -> bool:
        """Check if the monitoring system is accessible"""
        try:
            if not self.session:
                return False
            
            async with self.session.get(f"{self.config.url}/api/health") as response:
                return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False