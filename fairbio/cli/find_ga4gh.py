#!/usr/bin/env python3
"""
CLI tool to query GA4GH Service Registry.

This tool provides comprehensive access to the GA4GH Service Registry,
allowing discovery of services, filtering by type, and retrieving service details.

Reference: https://github.com/ga4gh-discovery/ga4gh-service-registry
OpenAPI: https://raw.githubusercontent.com/ga4gh-discovery/ga4gh-service-registry/develop/service-registry.yaml

Installation:
    pip install -e .

Usage:
    fairbio-ga4gh-registry [command] [options]
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

from fairbio.registries.ga4gh_registry import GA4GHServiceRegistry


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s'
    )
    return logging.getLogger(__name__)


def save_output(data, output_file: str, format: str = "json"):
    """Save output to file in specified format."""
    if format == "json":
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    elif format == "text":
        with open(output_file, 'w') as f:
            if isinstance(data, dict):
                f.write(json.dumps(data, indent=2))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        f.write(json.dumps(item) + "\n")
                    else:
                        f.write(str(item) + "\n")
            else:
                f.write(str(data))


def cmd_list_services(args):
    """List all services or filter by type."""
    logger = setup_logging(args.verbose)
    logger.info("🔍 Fetching services from GA4GH Service Registry...")
    
    try:
        registry = GA4GHServiceRegistry(args.registry)
        
        # Get all services
        all_services = registry.get_services()
        logger.info(f"✓ Found {len(all_services)} total services")
        
        # Filter by type if specified
        if args.type:
            logger.info(f"🔎 Filtering by type: {args.type}")
            filtered_services = registry.get_services_by_type(args.type)
            logger.info(f"✓ Found {len(filtered_services)} services of type '{args.type}'")
            services = filtered_services
        else:
            services = all_services
        
        # Prepare output
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(services),
            "filter_type": args.type if args.type else None,
            "services": services
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print summary
        logger.info("\n📋 Services Summary:")
        for i, service in enumerate(services[:10], 1):  # Show first 10
            logger.info(f"  {i}. {service.get('id', 'Unknown')} - {service.get('name', 'N/A')}")
        if len(services) > 10:
            logger.info(f"  ... and {len(services) - 10} more")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_service(args):
    """Get a specific service by ID."""
    logger = setup_logging(args.verbose)
    
    if not args.id:
        logger.error("❌ Service ID is required (use --id)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching service: {args.id}")
    
    try:
        registry = GA4GHServiceRegistry(args.registry)
        service = registry.get_service_by_id(args.id)
        
        if not service:
            logger.error(f"❌ Service not found: {args.id}")
            sys.exit(1)
        
        logger.info(f"✓ Found service: {service.get('name', args.id)}")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "service": service
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print details
        logger.info("\n📋 Service Details:")
        logger.info(f"  ID: {service.get('id', 'N/A')}")
        logger.info(f"  Name: {service.get('name', 'N/A')}")
        logger.info(f"  URL: {service.get('url', 'N/A')}")
        logger.info(f"  Description: {service.get('description', 'N/A')}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_list_types(args):
    """List all service types."""
    logger = setup_logging(args.verbose)
    logger.info("🔍 Fetching service types from GA4GH Service Registry...")
    
    try:
        registry = GA4GHServiceRegistry(args.registry)
        service_types = registry.get_service_types()
        
        logger.info(f"✓ Found {len(service_types)} service types")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_types": len(service_types),
            "service_types": service_types
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print types
        logger.info("\n📋 Service Types:")
        for i, svc_type in enumerate(service_types, 1):
            group = svc_type.get('group', 'N/A')
            artifact = svc_type.get('artifact', 'N/A')
            version = svc_type.get('version', 'N/A')
            logger.info(f"  {i}. {artifact} (v{version}) - {group}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_registry_info(args):
    """Get information about the registry itself."""
    logger = setup_logging(args.verbose)
    logger.info("🔍 Fetching registry information...")
    
    try:
        registry = GA4GHServiceRegistry(args.registry)
        registry_info = registry.get_service_info()
        
        if not registry_info:
            logger.error("❌ Could not retrieve registry information")
            sys.exit(1)
        
        logger.info(f"✓ Retrieved registry info")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_info": registry_info
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print info
        logger.info("\n📋 Registry Information:")
        logger.info(f"  ID: {registry_info.get('id', 'N/A')}")
        logger.info(f"  Name: {registry_info.get('name', 'N/A')}")
        logger.info(f"  URL: {registry_info.get('url', 'N/A')}")
        logger.info(f"  Organization: {registry_info.get('organization', {}).get('name', 'N/A')}")
        logger.info(f"  Description: {registry_info.get('description', 'N/A')}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="fairbio-ga4gh-registry",
        description="Query GA4GH Service Registry for services and service types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  services    List all services (or filter by type)
  service     Get a specific service by ID
  types       List all service types
  info        Get registry information

Examples:
  fairbio-ga4gh-registry services
  fairbio-ga4gh-registry services --type trs -o trs_services.json
  fairbio-ga4gh-registry service --id org.dockstore.dockstoreapi -o dockstore.json
  fairbio-ga4gh-registry types -o service_types.json
  fairbio-ga4gh-registry info
  fairbio-ga4gh-registry services --type wes -f text -o wes_services.txt

Reference:
  https://github.com/ga4gh-discovery/ga4gh-service-registry
        """
    )
    
    # Global options
    parser.add_argument(
        "-r", "--registry",
        metavar="URL",
        help="Custom GA4GH Service Registry URL"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="fairbio-ga4gh-registry 0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Services command
    services_parser = subparsers.add_parser('services', help='List services')
    services_parser.add_argument(
        '-t', '--type',
        metavar='TYPE',
        help='Filter services by type (e.g., trs, wes, tes)'
    )
    services_parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Save results to file'
    )
    services_parser.add_argument(
        '-f', '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    services_parser.set_defaults(func=cmd_list_services)
    
    # Service command (singular - get by ID)
    service_parser = subparsers.add_parser('service', help='Get service by ID')
    service_parser.add_argument(
        '-i', '--id',
        metavar='ID',
        help='Service ID to retrieve'
    )
    service_parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Save results to file'
    )
    service_parser.add_argument(
        '-f', '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    service_parser.set_defaults(func=cmd_get_service)
    
    # Types command
    types_parser = subparsers.add_parser('types', help='List service types')
    types_parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Save results to file'
    )
    types_parser.add_argument(
        '-f', '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    types_parser.set_defaults(func=cmd_list_types)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get registry information')
    info_parser.add_argument(
        '-o', '--output',
        metavar='FILE',
        help='Save results to file'
    )
    info_parser.add_argument(
        '-f', '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)'
    )
    info_parser.set_defaults(func=cmd_registry_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
