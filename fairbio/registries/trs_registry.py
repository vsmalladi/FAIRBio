"""
Tool Registry Service (TRS) Client

This module provides utilities for interacting with GA4GH Tool Registry Service (TRS) endpoints.
TRS is a standard API for discovering and accessing tools (workflows and tasks) in tool registries.

Reference: https://github.com/ga4gh/tool-registry-service-schemas
OpenAPI Specification: https://raw.githubusercontent.com/ga4gh/tool-registry-service-schemas/develop/openapi/openapi.yaml
"""

import requests
import json
from urllib.parse import urlparse, parse_qs


class ToolRegistryService(object):
    """Client for interacting with GA4GH Tool Registry Service (TRS).
    
    Implements the TRS API specification for discovering and retrieving tools,
    tool versions, descriptors, and related metadata from TRS-compliant registries.
    """
    
    # Standard TRS API path suffix (most registries use /ga4gh/trs/v2)
    TRS_API_PATH = "/ga4gh/trs/v2"
    
    def __init__(self, registry_url):
        """
        Initialize TRS client.
        
        Args:
            registry_url (str): Base URL of the TRS registry (e.g., https://dockstore.org)
                              Can include the full path or just the base URL.
        """
        # Remove trailing slash and TRS path if present
        self.registry_url = registry_url.rstrip('/')
        if self.registry_url.endswith(self.TRS_API_PATH):
            self.registry_url = self.registry_url[:-len(self.TRS_API_PATH)]
        
        # Construct the full TRS endpoint
        self.trs_url = self.registry_url + self.TRS_API_PATH
        self.session = requests.Session()
    
    def get_service_info(self):
        """
        Get information about the TRS service.
        
        GET /service-info
        
        Returns:
            dict: Service information including name, version, and organization
        """
        try:
            url = "{0}/service-info".format(self.trs_url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching TRS service info: {0}".format(e))
            return None
    
    def get_tools(self, limit=100, offset=0, **filters):
        """
        List all tools in the registry with optional filtering.
        
        GET /tools
        
        Args:
            limit (int): Maximum number of tools to return (default: 1000)
            offset (str): Start index of paging
            **filters: Additional filter parameters:
                - id (str): Unique tool identifier
                - alias (str): Tool alias
                - toolClass (str): Filter by tool class
                - descriptorType (str): Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)
                - tags (list): Registry-specific tags
                - registry (str): Image registry
                - organization (str): Organization in registry
                - name (str): Tool name
                - toolname (str): Tool name
                - description (str): Tool description
                - author (str): Tool author
                - checker (bool): Return only checker workflows
        
        Returns:
            dict: Response containing tools list and pagination headers
        """
        try:
            url = "{0}/tools".format(self.trs_url)
            # Normalize case-insensitive client filters to TRS spec casing
            if "toolclass" in filters and "toolClass" not in filters:
                filters["toolClass"] = filters.pop("toolclass")
            if "descriptortype" in filters and "descriptorType" not in filters:
                filters["descriptorType"] = filters.pop("descriptortype")

            params = {"limit": limit}
            if offset is not None:
                params["offset"] = offset
            
            # Add any additional filters
            params.update(filters)
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return {
                "tools": response.json(),  # body is a plain array
                # pagination info is in headers:
                "next_page": response.headers.get("next_page"),
                "last_page": response.headers.get("last_page"),
                "self_link": response.headers.get("self_link"),
                "current_offset": response.headers.get("current_offset"),
                "current_limit": response.headers.get("current_limit"),
            }
        except requests.RequestException as e:
            print("Error fetching tools: {0}".format(e))
            return []
    
    def get_all_tools(self, limit=100, **filters):
        """
        Fetch ALL tools from the registry by automatically paginating through results.
        
        This method automatically handles pagination and combines all results.
        
        Args:
            limit (int): Page size for each request (default: 1000)
            **filters: Additional filter parameters (same as get_tools)
        
        Returns:
            dict: Response with all_tools list, total_count, and pagination summary
        """
        try:
            page_size = min(limit, 100)
            all_tools = []
            
            # Use next_page URL from headers rather than manually incrementing offset
            next_url = None
            offset = 0
            
            while True:
                if next_url:
                    # Use the server-provided next_page URL directly
                    response = self.session.get(next_url)
                else:
                    response = self.session.get(
                        f"{self.trs_url}/tools",
                        params={"limit": page_size, "offset": offset, **filters}
                    )
                
                response.raise_for_status()
                page_tools = response.json()  # body is a plain array per spec
                
                if not page_tools:
                    break
                    
                all_tools.extend(page_tools)
                
                # Pagination state lives in HEADERS, not the body
                next_url = response.headers.get("next_page")
                
                if not next_url or len(page_tools) < page_size:
                    break
            
            return {
                "all_tools": all_tools,
                "total_count": len(all_tools),
                "total_pages": (len(all_tools) + page_size - 1) // page_size,
                "page_size": page_size,
            }
        except requests.RequestException as e:
            print("Error fetching all tools: {0}".format(e))
            return {"all_tools": [], "total_count": 0, "total_pages": 0}
    
    def get_tool(self, tool_id):
        """
        Retrieve a specific tool by ID.
        
        GET /tools/{id}
        
        Args:
            tool_id (str): Unique identifier of the tool
        
        Returns:
            dict: Tool information including versions
        """
        try:
            url = "{0}/tools/{1}".format(self.trs_url, tool_id)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching tool '{0}': {1}".format(tool_id, e))
            return None
    
    def get_tool_versions(self, tool_id):
        """
        List all versions of a specific tool.
        
        GET /tools/{id}/versions
        
        Args:
            tool_id (str): Unique identifier of the tool
        
        Returns:
            list: List of tool versions
        """
        try:
            url = "{0}/tools/{1}/versions".format(self.trs_url, tool_id)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching versions for tool '{0}': {1}".format(tool_id, e))
            return []
    
    def get_tool_version(self, tool_id, version_id):
        """
        Retrieve a specific version of a tool.
        
        GET /tools/{id}/versions/{version_id}
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier (e.g., 'v1.0.0')
        
        Returns:
            dict: Tool version information
        """
        try:
            url = "{0}/tools/{1}/versions/{2}".format(self.trs_url, tool_id, version_id)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching tool version '{0}' for tool '{1}': {2}".format(
                version_id, tool_id, e))
            return None
    
    def get_tool_descriptor(self, tool_id, version_id, descriptor_type):
        """
        Get the tool descriptor for a specific version.
        
        GET /tools/{id}/versions/{version_id}/{type}/descriptor
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier
            descriptor_type (str): Descriptor type (CWL, WDL, NFL, GALAXY, SMK, PLAIN_CWL, PLAIN_WDL, etc.)
        
        Returns:
            dict: File wrapper containing descriptor content
        """
        try:
            url = "{0}/tools/{1}/versions/{2}/{3}/descriptor".format(
                self.trs_url, tool_id, version_id, descriptor_type)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching {0} descriptor for tool '{1}' version '{2}': {3}".format(
                descriptor_type, tool_id, version_id, e))
            return None
    
    def get_tool_descriptor_by_path(self, tool_id, version_id, descriptor_type, relative_path):
        """
        Get additional tool descriptor files by relative path.
        
        GET /tools/{id}/versions/{version_id}/{type}/descriptor/{relative_path}
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier
            descriptor_type (str): Descriptor type
            relative_path (str): Relative path to the descriptor file
        
        Returns:
            dict: File wrapper containing descriptor content
        """
        try:
            url = "{0}/tools/{1}/versions/{2}/{3}/descriptor/{4}".format(
                self.trs_url, tool_id, version_id, descriptor_type, relative_path)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching descriptor file '{0}': {1}".format(relative_path, e))
            return None
    
    def get_tool_tests(self, tool_id, version_id, descriptor_type):
        """
        Get test files for a specific tool version.
        
        GET /tools/{id}/versions/{version_id}/{type}/tests
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier
            descriptor_type (str): Descriptor type
        
        Returns:
            list: List of test file wrappers
        """
        try:
            url = "{0}/tools/{1}/versions/{2}/{3}/tests".format(
                self.trs_url, tool_id, version_id, descriptor_type)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching tests for tool '{0}' version '{1}': {2}".format(
                tool_id, version_id, e))
            return []
    
    def get_tool_files(self, tool_id, version_id, descriptor_type, format=None):
        """
        Get a list of files for a tool version.
        
        GET /tools/{id}/versions/{version_id}/{type}/files
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier
            descriptor_type (str): Descriptor type
            format (str): Optional format ('zip' to get all files as a zip)
        
        Returns:
            list or bytes: List of tool files or zip file content
        """
        try:
            url = "{0}/tools/{1}/versions/{2}/{3}/files".format(
                self.trs_url, tool_id, version_id, descriptor_type)
            params = {}
            if format:
                params['format'] = format
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Return raw bytes if zip format requested
            if format == 'zip':
                return response.content
            return response.json()
        except requests.RequestException as e:
            print("Error fetching files for tool '{0}' version '{1}': {2}".format(
                tool_id, version_id, e))
            return [] if not format else None
    
    def get_tool_containerfile(self, tool_id, version_id):
        """
        Get container specification(s) for a tool version.
        
        GET /tools/{id}/versions/{version_id}/containerfile
        
        Args:
            tool_id (str): Unique identifier of the tool
            version_id (str): Version identifier
        
        Returns:
            list: List of container file wrappers (e.g., Dockerfiles, Singularity recipes)
        """
        try:
            url = "{0}/tools/{1}/versions/{2}/containerfile".format(
                self.trs_url, tool_id, version_id)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching containerfile for tool '{0}' version '{1}': {2}".format(
                tool_id, version_id, e))
            return []
    
    def get_tool_classes(self):
        """
        List all tool classes available in the registry.
        
        GET /toolClasses
        
        Returns:
            list: List of tool classes (e.g., CommandLineTool, Workflow)
        """
        try:
            url = "{0}/toolClasses".format(self.trs_url)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("Error fetching tool classes: {0}".format(e))
            return []
    
    def search_tools(self, query=None, descriptor_type=None, author=None, limit=1000):
        """
        Search for tools using common filters.
        
        Convenience method that combines get_tools() with common search parameters.
        
        Args:
            query (str): Search term (matches name, description, or toolname)
            descriptor_type (str): Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)
            author (str): Filter by tool author
            limit (int): Maximum number of results
        
        Returns:
            list: List of matching tools
        """
        filters = {"limit": limit}
        if query:
            filters["name"] = query
        if descriptor_type:
            filters["descriptorType"] = descriptor_type
        if author:
            filters["author"] = author
        
        result = self.get_tools(**filters)
        return result if isinstance(result, list) else result.get("tools", [])
