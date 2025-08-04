import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MonitoringConfig:
    url: str
    token: str = ""
    username: str = ""
    password: str = ""
    timeout: int = 30

class Config:
    def __init__(self):
        self.monitoring_systems = {
            "grafana": MonitoringConfig(
                url=os.getenv("GRAFANA_URL", "http://localhost:3000"),
                token=os.getenv("GRAFANA_TOKEN", ""),
                username=os.getenv("GRAFANA_USERNAME", "admin"),
                password=os.getenv("GRAFANA_PASSWORD", "")
            ),
            "prometheus": MonitoringConfig(
                url=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
                token=os.getenv("PROMETHEUS_TOKEN", "")
            ),
            "elasticsearch": MonitoringConfig(
                url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
                username=os.getenv("ELASTICSEARCH_USERNAME", "elastic"),
                password=os.getenv("ELASTICSEARCH_PASSWORD", "")
            ),
            "nagios": MonitoringConfig(
                url=os.getenv("NAGIOS_URL", "http://localhost/nagios"),
                username=os.getenv("NAGIOS_USERNAME", "nagiosadmin"),
                password=os.getenv("NAGIOS_PASSWORD", "")
            )
        }
    
    def get_system_config(self, system_name: str) -> MonitoringConfig:
        return self.monitoring_systems.get(system_name)

# Global config instance
config = Config()