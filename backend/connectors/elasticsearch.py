from typing import List, Dict, Any
from datetime import datetime
import json
from .base import MonitoringConnector

class ElasticsearchConnector(MonitoringConnector):
    async def get_recent_deployments(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query Elasticsearch for deployment logs"""
        if not self.session:
            return []
        
        try:
            # Example query - adjust based on your log structure
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": end_time.isoformat()
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {"match": {"message": "deployment"}},
                                        {"match": {"message": "deploy"}},
                                        {"match": {"kubernetes.labels.app": "*"}},
                                        {"match": {"container.name": "*"}}
                                    ]
                                }
                            }
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 50
            }
            
            auth = None
            if self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            
            async with self.session.post(
                f"{self.config.url}/_search",
                json=query,
                auth=auth
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    deployments = []
                    
                    for hit in data.get("hits", {}).get("hits", []):
                        source = hit.get("_source", {})
                        deployments.append({
                            "service": source.get("kubernetes", {}).get("labels", {}).get("app", "unknown"),
                            "version": source.get("kubernetes", {}).get("labels", {}).get("version", "unknown"),
                            "timestamp": source.get("@timestamp"),
                            "author": source.get("kubernetes", {}).get("labels", {}).get("deployed_by", "unknown"),
                            "status": "success" if "error" not in source.get("message", "").lower() else "failed"
                        })
                    
                    return deployments
                    
        except Exception as e:
            print(f"Error querying Elasticsearch for deployments: {e}")
        
        return []
    
    async def get_metric_anomalies(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """This would typically come from Prometheus, but we can check for performance logs"""
        if not self.session:
            return []
        
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": end_time.isoformat()
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {"range": {"response_time": {"gte": 1000}}},
                                        {"range": {"duration": {"gte": 5000}}},
                                        {"match": {"message": "slow query"}},
                                        {"match": {"message": "timeout"}}
                                    ]
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "services": {
                        "terms": {"field": "service.keyword"},
                        "aggs": {
                            "avg_response_time": {"avg": {"field": "response_time"}}
                        }
                    }
                },
                "size": 0
            }
            
            auth = None
            if self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            
            async with self.session.post(
                f"{self.config.url}/_search",
                json=query,
                auth=auth
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    anomalies = []
                    
                    for bucket in data.get("aggregations", {}).get("services", {}).get("buckets", []):
                        service = bucket.get("key")
                        avg_response = bucket.get("avg_response_time", {}).get("value", 0)
                        
                        if avg_response > 500:  # Threshold for anomaly
                            anomalies.append({
                                "metric": "response_time_avg",
                                "service": service,
                                "current_value": round(avg_response, 2),
                                "baseline": 200,  # This should come from historical data
                                "severity": "high" if avg_response > 1000 else "medium",
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    return anomalies
                    
        except Exception as e:
            print(f"Error querying Elasticsearch for anomalies: {e}")
        
        return []
    
    async def get_error_spikes(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query for error logs and spikes"""
        if not self.session:
            return []
        
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": end_time.isoformat()
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {"match": {"level": "ERROR"}},
                                        {"match": {"level": "FATAL"}},
                                        {"match": {"message": "exception"}},
                                        {"match": {"message": "error"}},
                                        {"range": {"status_code": {"gte": 400}}}
                                    ]
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "error_types": {
                        "terms": {"field": "error.type.keyword", "size": 10},
                        "aggs": {
                            "services": {"terms": {"field": "service.keyword"}},
                            "first_occurrence": {"min": {"field": "@timestamp"}}
                        }
                    }
                },
                "size": 100
            }
            
            auth = None
            if self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            
            async with self.session.post(
                f"{self.config.url}/_search",
                json=query,
                auth=auth
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    errors = []
                    
                    for bucket in data.get("aggregations", {}).get("error_types", {}).get("buckets", []):
                        error_type = bucket.get("key", "Unknown")
                        count = bucket.get("doc_count", 0)
                        first_seen = bucket.get("first_occurrence", {}).get("value_as_string")
                        
                        # Get the most common service for this error
                        services = bucket.get("services", {}).get("buckets", [])
                        service = services[0].get("key", "unknown") if services else "unknown"
                        
                        # Get a sample message
                        sample_message = "Error details not available"
                        if data.get("hits", {}).get("hits"):
                            sample_message = data["hits"]["hits"][0].get("_source", {}).get("message", sample_message)
                        
                        errors.append({
                            "service": service,
                            "error_type": error_type,
                            "count": count,
                            "first_seen": first_seen,
                            "sample_message": sample_message
                        })
                    
                    return errors
                    
        except Exception as e:
            print(f"Error querying Elasticsearch for errors: {e}")
        
        return []
    
    async def get_alerts(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query for alert-related logs"""
        if not self.session:
            return []
        
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time.isoformat(),
                                        "lte": end_time.isoformat()
                                    }
                                }
                            },
                            {
                                "bool": {
                                    "should": [
                                        {"match": {"message": "alert"}},
                                        {"match": {"message": "critical"}},
                                        {"match": {"message": "warning"}},
                                        {"match": {"alertname": "*"}}
                                    ]
                                }
                            }
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 20
            }
            
            auth = None
            if self.config.username and self.config.password:
                auth = aiohttp.BasicAuth(self.config.username, self.config.password)
            
            async with self.session.post(
                f"{self.config.url}/_search",
                json=query,
                auth=auth
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = []
                    
                    for hit in data.get("hits", {}).get("hits", []):
                        source = hit.get("_source", {})
                        alerts.append({
                            "service": source.get("service", source.get("instance", "unknown")),
                            "alert": source.get("alertname", source.get("message", "Unknown Alert")),
                            "status": source.get("status", "UNKNOWN").upper(),
                            "timestamp": source.get("@timestamp"),
                            "duration": "unknown"
                        })
                    
                    return alerts
                    
        except Exception as e:
            print(f"Error querying Elasticsearch for alerts: {e}")
        
        return []