"""
GA4GH Service Registry Client

This module provides utilities for discovering GA4GH services including
TRS (Tool Registry Service), WES, and other GA4GH-compliant services.

Reference: https://github.com/ga4gh-discovery/ga4gh-service-registry
Specification: https://raw.githubusercontent.com/ga4gh-discovery/ga4gh-service-registry/develop/service-registry.yaml
"""

import requests
import json


class GA4GHServiceRegistry(object):
    """Client for interacting with GA4GH Service Registry.
    
    Implements the GA4GH Service Registry API specification for discovering
    GA4GH services across organizational boundaries.
    """
    
    # GA4GH Service Registry endpoint
    SERVICE_REGISTRY_URL = "https://registry.ga4gh.org/v1"

    def __init__(self, registry_url=None):
        """
        Initialize GA4GH Service Registry client.
        
        Args:
            registry_url (str): Base URL of the GA4GH service registry (default: official GA4GH registry)
        """
        if registry_url is None:
            registry_url = self.SERVICE_REGISTRY_URL
        # Ensure registry URL has trailing slash for proper path joining
        self.registry_url = registry_url.rstrip('/') + '/'
        self.session = requests.Session()
    
    def get_services(self):
        """
        List all services in the registry.
        
        GET /services
        
        Returns:
            list: List of service configurations with metadata
        """
        try:
            url = "{0}services".format(self.registry_url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching services: {0}".format(e))
            return []
    
    def get_service_by_id(self, service_id):
        """
        Find a specific service in the registry by ID.
        
        GET /services/{serviceId}
        
        Args:
            service_id (str): ID of the service to retrieve
            
        Returns:
            dict: Service information dictionary
        """
        try:
            url = "{0}services/{1}".format(self.registry_url, service_id)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching service info: {0}".format(e))
            return None
    
    def get_service_types(self):
        """
        List all distinct service types exposed by the registry.
        
        GET /services/types
        
        Returns:
            list: List of service type configurations
        """
        try:
            url = "{0}services/types".format(self.registry_url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching service types: {0}".format(e))
            return []
    
    def get_service_info(self):
        """
        Get information about this service registry itself.
        
        GET /service-info
        
        Returns:
            dict: Service information about the registry
        """
        try:
            url = "{0}service-info".format(self.registry_url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching registry info: {0}".format(e))
            return None
    
    def get_services_by_type(self, service_type):
        """
        Filter services by type (convenience method).
        
        Args:
            service_type (str): Type of service to filter for (e.g., 'trs', 'wes', 'tes')
            
        Returns:
            list: List of services matching the specified type
        """
        all_services = self.get_services()
        if not all_services:
            return []
        
        filtered = []
        for service in all_services:
            service_type_obj = service.get("type", {})
            if isinstance(service_type_obj, dict):
                artifact = service_type_obj.get("artifact", "")
                # Extract the service name from artifact (e.g., "tool-registry-service" -> "trs")
                if service_type in artifact or service_type.lower() in str(service_type_obj).lower():
                    filtered.append(service)
            elif isinstance(service_type_obj, str):
                if service_type.lower() in service_type_obj.lower():
                    filtered.append(service)
        
        return filtered
