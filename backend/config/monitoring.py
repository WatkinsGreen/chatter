import os
from typing import Dict, Any

class MonitoringConfig:
    """Configuration for monitoring systems"""
    
    @staticmethod
    def get_systems() -> Dict[str, Dict[str, Any]]:
        """Get monitoring systems configuration from environment variables"""
        return {
            "grafana": {
                "url": os.getenv("GRAFANA_URL", "http://localhost:3000"),
                "token": os.getenv("GRAFANA_TOKEN", ""),
                "enabled": os.getenv("GRAFANA_ENABLED", "true").lower() == "true",
                "timeout": int(os.getenv("GRAFANA_TIMEOUT", "30"))
            },
            "prometheus": {
                "url": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
                "token": os.getenv("PROMETHEUS_TOKEN", ""),
                "enabled": os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
                "timeout": int(os.getenv("PROMETHEUS_TIMEOUT", "30"))
            },
            "elasticsearch": {
                "url": os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
                "token": os.getenv("ELASTICSEARCH_TOKEN", ""),
                "username": os.getenv("ELASTICSEARCH_USERNAME", ""),
                "password": os.getenv("ELASTICSEARCH_PASSWORD", ""),
                "enabled": os.getenv("ELASTICSEARCH_ENABLED", "true").lower() == "true",
                "timeout": int(os.getenv("ELASTICSEARCH_TIMEOUT", "30"))
            },
            "nagios": {
                "url": os.getenv("NAGIOS_URL", "http://localhost/nagios"),
                "token": os.getenv("NAGIOS_TOKEN", ""),
                "username": os.getenv("NAGIOS_USERNAME", ""),
                "password": os.getenv("NAGIOS_PASSWORD", ""),
                "enabled": os.getenv("NAGIOS_ENABLED", "true").lower() == "true",
                "timeout": int(os.getenv("NAGIOS_TIMEOUT", "30"))
            },
            "datadog": {
                "url": os.getenv("DATADOG_URL", "https://api.datadoghq.com"),
                "api_key": os.getenv("DATADOG_API_KEY", ""),
                "app_key": os.getenv("DATADOG_APP_KEY", ""),
                "enabled": os.getenv("DATADOG_ENABLED", "false").lower() == "true",
                "timeout": int(os.getenv("DATADOG_TIMEOUT", "30"))
            },
            "newrelic": {
                "url": os.getenv("NEWRELIC_URL", "https://api.newrelic.com"),
                "api_key": os.getenv("NEWRELIC_API_KEY", ""),
                "enabled": os.getenv("NEWRELIC_ENABLED", "false").lower() == "true",
                "timeout": int(os.getenv("NEWRELIC_TIMEOUT", "30"))
            },
            "splunk": {
                "url": os.getenv("SPLUNK_URL", "http://localhost:8089"),
                "token": os.getenv("SPLUNK_TOKEN", ""),
                "username": os.getenv("SPLUNK_USERNAME", ""),
                "password": os.getenv("SPLUNK_PASSWORD", ""),
                "enabled": os.getenv("SPLUNK_ENABLED", "false").lower() == "true",
                "timeout": int(os.getenv("SPLUNK_TIMEOUT", "30"))
            }
        }
    
    @staticmethod
    def get_enabled_systems() -> Dict[str, Dict[str, Any]]:
        """Get only enabled monitoring systems"""
        all_systems = MonitoringConfig.get_systems()
        return {name: config for name, config in all_systems.items() if config.get("enabled", True)}