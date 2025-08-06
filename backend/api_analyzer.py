import asyncio
import aiohttp
import json
import csv
import io
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from config.monitoring import MonitoringConfig

logger = logging.getLogger(__name__)

class APIDataAnalyzer:
    """Analyzes monitoring data from API endpoints and routes to appropriate dashboards"""
    
    def __init__(self):
        self.api_endpoints = MonitoringConfig.get_api_endpoints()
        self.dashboard_routing = MonitoringConfig.get_dashboard_routing()
        
        # Dynamic API URL patterns
        self.dynamic_urls = {
            "customer": "http://10.10.4.6/dashboards/customers/index.html?raw=true&customer={customer}",
            "environment": "http://10.10.4.6/dashboards/environment/index.html?raw=true&env={environment}",
            "performance": "http://10.10.4.6/dashboards/performance/index.html?raw=true&service={service}",
        }
        
    async def fetch_api_data(self, system: str, endpoint_type: str, **params) -> Optional[Dict[str, Any]]:
        """Fetch data from monitoring system API"""
        if system not in self.api_endpoints:
            logger.warning(f"System {system} not configured")
            return None
            
        system_config = self.api_endpoints[system]
        api_url = system_config.get(f"{endpoint_type}_api")
        
        if not api_url:
            logger.warning(f"No {endpoint_type} API configured for {system}")
            return None
            
        try:
            headers = {}
            auth = None
            
            # Configure authentication based on system
            if system == "grafana":
                api_key = system_config.get("api_key")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                    
            elif system == "nagios":
                api_user = system_config.get("api_user")
                api_pass = system_config.get("api_pass")
                if api_user and api_pass:
                    auth = aiohttp.BasicAuth(api_user, api_pass)
                    
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=headers, auth=auth, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed: {response.status} - {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching {system} {endpoint_type} data: {e}")
            return None
    
    async def analyze_grafana_metrics(self, time_range: str = "2h") -> Dict[str, Any]:
        """Analyze Grafana metrics and determine appropriate dashboards"""
        
        # Fetch metrics data from Grafana API
        metrics_data = await self.fetch_api_data("grafana", "metrics", 
                                                range=time_range, 
                                                step="5m")
        
        if not metrics_data:
            return {"dashboards": [], "metrics": [], "alerts": []}
            
        analysis = {
            "dashboards": [],
            "metrics": [],
            "alerts": [],
            "recommendations": []
        }
        
        # Analyze metrics to determine which dashboards are relevant
        # This will be implemented based on your specific API response structure
        logger.info(f"Analyzed Grafana metrics: {len(metrics_data.get('data', {}).get('result', []))} series")
        
        return analysis
        
    async def analyze_nagios_status(self) -> Dict[str, Any]:
        """Analyze Nagios service/host status"""
        
        # Fetch services and hosts data
        services_data = await self.fetch_api_data("nagios", "services")
        hosts_data = await self.fetch_api_data("nagios", "hosts")
        
        analysis = {
            "critical_services": [],
            "warning_services": [],
            "critical_hosts": [],
            "warning_hosts": [],
            "dashboard_urls": []
        }
        
        if services_data:
            # Analyze service states and build appropriate dashboard URLs
            logger.info(f"Analyzed Nagios services: {len(services_data.get('services', []))}")
            
        if hosts_data:
            # Analyze host states
            logger.info(f"Analyzed Nagios hosts: {len(hosts_data.get('hosts', []))}")
            
        return analysis
    
    def build_dashboard_url(self, system: str, dashboard_type: str, **params) -> Optional[str]:
        """Build specific dashboard URL based on analysis results"""
        
        if system not in self.dashboard_routing:
            return None
            
        system_dashboards = self.dashboard_routing[system]
        base_url = system_dashboards.get(dashboard_type)
        
        if not base_url:
            return None
            
        # Add parameters to URL
        if params:
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            connector = "&" if "?" in base_url else "?"
            return f"{base_url}{connector}{param_string}"
            
        return base_url
    
    async def get_intelligent_dashboard_urls(self, context: str = "") -> Dict[str, str]:
        """Get dashboard URLs based on current system state and context"""
        
        urls = {}
        
        # Analyze current state of monitoring systems
        grafana_analysis = await self.analyze_grafana_metrics()
        nagios_analysis = await self.analyze_nagios_status()
        
        # Build intelligent dashboard URLs based on analysis
        
        # Deployment dashboards
        if grafana_analysis.get("metrics"):
            urls["deployments"] = self.build_dashboard_url("grafana", "deployment_dashboard", 
                                                         from_time="now-2h", to_time="now")
        
        # Performance dashboards
        if grafana_analysis.get("alerts"):
            urls["performance"] = self.build_dashboard_url("grafana", "performance_dashboard",
                                                         from_time="now-1h", to_time="now")
        
        # Error dashboards
        urls["errors"] = self.build_dashboard_url("grafana", "error_dashboard")
        
        # Nagios tactical overview
        if nagios_analysis.get("critical_services") or nagios_analysis.get("warning_services"):
            urls["system_health"] = self.build_dashboard_url("nagios", "tactical_overview")
            
        return urls

    async def fetch_customer_data(self, customer_name: str) -> Optional[Dict[str, Any]]:
        """Fetch customer-specific monitoring data"""
        url = self.dynamic_urls["customer"].format(customer=customer_name)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        csv_text = await response.text()
                        return self.parse_customer_csv(csv_text, customer_name)
                    else:
                        logger.error(f"Customer API request failed: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching customer data for {customer_name}: {e}")
            return None
    
    def parse_customer_csv(self, csv_text: str, customer_name: str) -> Dict[str, Any]:
        """Parse CSV customer data into structured format"""
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            customer_records = []
            
            for row in csv_reader:
                # Expected fields: customer, environment, dbinstance, reportpath, hotticket_reason, cid, compeatapp, isVIP
                customer_record = {
                    "customer": row.get("customer", ""),
                    "environment": row.get("environment", ""),
                    "dbinstance": row.get("dbinstance", ""),
                    "reportpath": row.get("reportpath", ""),
                    "hotticket_reason": row.get("hotticket_reason", ""),
                    "cid": row.get("cid", ""),
                    "compeatapp": row.get("compeatapp", ""),
                    "isVIP": row.get("isVIP", "").lower() == "true"
                }
                customer_records.append(customer_record)
            
            # Create analysis structure
            analysis = {
                "customer_name": customer_name,
                "total_records": len(customer_records),
                "environments": list(set(r["environment"] for r in customer_records if r["environment"])),
                "database_instances": list(set(r["dbinstance"] for r in customer_records if r["dbinstance"])),
                "hot_tickets": [r for r in customer_records if r["hotticket_reason"]],
                "vip_status": any(r["isVIP"] for r in customer_records),
                "raw_records": customer_records
            }
            
            logger.info(f"Parsed customer data for {customer_name}: {len(customer_records)} records, VIP: {analysis['vip_status']}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error parsing customer CSV data: {e}")
            return {"error": str(e), "customer_name": customer_name, "raw_data": csv_text}
    
    async def analyze_for_conversation_context(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze monitoring data based on conversation context (customer, environment, etc.)"""
        
        analysis_results = {
            "monitoring_data": {},
            "dashboard_urls": {},
            "ai_context": {},
            "recommendations": []
        }
        
        # Check what context we have from the conversation
        customer = conversation_context.get("customer")
        environment = conversation_context.get("environment") 
        issue_type = conversation_context.get("issue_type")
        
        # Fetch relevant data based on context
        if customer:
            customer_data = await self.fetch_customer_data(customer)
            if customer_data:
                analysis_results["monitoring_data"]["customer"] = customer_data
                analysis_results["dashboard_urls"]["customer"] = f"http://10.10.4.6/dashboards/customers/detail.html?customer={customer}"
                
                # Build AI context from customer data
                analysis_results["ai_context"]["customer_summary"] = f"""
Customer: {customer}
VIP Status: {'Yes' if customer_data.get('vip_status') else 'No'}
Environments: {', '.join(customer_data.get('environments', []))}
Database Instances: {', '.join(customer_data.get('database_instances', []))}
Active Hot Tickets: {len(customer_data.get('hot_tickets', []))}
Hot Ticket Reasons: {', '.join([t.get('hotticket_reason', '') for t in customer_data.get('hot_tickets', [])])}
"""
                
        logger.info(f"Context analysis complete - Customer: {customer}, Environment: {environment}, Issue: {issue_type}")
        return analysis_results

# Global instance
api_analyzer = APIDataAnalyzer()