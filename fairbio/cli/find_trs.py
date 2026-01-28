#!/usr/bin/env python3
"""
CLI tool to query GA4GH Tool Registry Service (TRS) endpoints.

This tool provides comprehensive access to Tool Registry Service APIs,
allowing discovery of tools, versions, descriptors, and test files.

Reference: https://github.com/ga4gh/tool-registry-service-schemas
OpenAPI: https://raw.githubusercontent.com/ga4gh/tool-registry-service-schemas/develop/openapi/openapi.yaml

Installation:
    pip install -e .

Usage:
    fairbio-trs [command] [options]
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

from fairbio.registries.trs_registry import ToolRegistryService


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


def print_json_output(data):
    """Print data as formatted JSON to stdout."""
    print(json.dumps(data, indent=2))


def cmd_list_tools(args):
    """List all tools or filter by criteria."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    # Use get_all_tools if --all flag is set
    if args.all:
        logger.info(f"🔍 Fetching ALL tools from {args.registry}...")
        logger.info("   (This may take a while, automatically paginating through all results...)")
    else:
        logger.info(f"🔍 Fetching tools from {args.registry}...")
    
    try:
        trs = ToolRegistryService(args.registry)
        
        # Build filters
        filters = {}
        if args.id:
            filters['id'] = args.id
        if args.name:
            filters['toolname'] = args.name
        if args.author:
            filters['author'] = args.author
        if args.description:
            filters['description'] = args.description
        if args.descriptor_type:
            filters['descriptorType'] = args.descriptor_type
        
        # Get tools - either all or paginated
        if args.all:
            response = trs.get_all_tools(limit=args.limit, **filters)
            tool_list = response.get('all_tools', [])
            total = response.get('total_count', 0)
            pagination_info = {
                'total_pages': response.get('total_pages'),
                'page_size': response.get('page_size'),
            }
        else:
            tools = trs.get_tools(limit=args.limit, offset=args.offset, **filters)
            
            # Extract pagination info from response headers
            pagination_info = {}
            if isinstance(tools, dict):
                tool_list = tools.get('tools', []) if 'tools' in tools else [tools] if tools else []
                # Try to get pagination headers from response
                pagination_info = {
                    'current_offset': tools.get('current_offset'),
                    'current_limit': tools.get('current_limit'),
                    'next_page': tools.get('next_page'),
                    'last_page': tools.get('last_page'),
                    'self_link': tools.get('self_link'),
                }
                total = len(tool_list)
            else:
                tool_list = tools if isinstance(tools, list) else []
                total = len(tool_list)
        
        logger.info(f"✓ Found {total} tools")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "pagination": {k: v for k, v in pagination_info.items() if v is not None},
            "total_tools": total,
            "filters": filters if filters else None,
            "tools": tool_list
        }
        
        # Print JSON to stdout if requested
        if args.json:
            print_json_output(output)
            return output
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print summary
        logger.info("\n📋 Tools Summary:")
        for i, tool in enumerate(tool_list[:10], 1):
            tool_id = tool.get('id', 'Unknown')
            name = tool.get('name', 'N/A')
            org = tool.get('organization', 'N/A')
            logger.info(f"  {i}. {tool_id}")
            logger.info(f"     Name: {name}, Org: {org}")
        if total > 10:
            logger.info(f"  ... and {total - 10} more")
        
        # Print pagination info
        if args.all:
            logger.info("\n📄 Pagination Summary:")
            logger.info(f"  Total Tools: {pagination_info.get('total_pages')} pages retrieved")
            logger.info(f"  Page Size: {pagination_info.get('page_size')}")
        elif pagination_info.get('current_offset') is not None:
            logger.info("\n📄 Pagination:")
            logger.info(f"  Current Offset: {pagination_info.get('current_offset')}")
            logger.info(f"  Current Limit: {pagination_info.get('current_limit')}")
            if pagination_info.get('next_page'):
                logger.info(f"  Next Page Available: Yes")
            if pagination_info.get('last_page'):
                logger.info(f"  Has Last Page: Yes")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_tool(args):
    """Get a specific tool by ID."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching tool: {args.id}")
    
    try:
        trs = ToolRegistryService(args.registry)
        tool = trs.get_tool(args.id)
        
        if not tool:
            logger.error(f"❌ Tool not found: {args.id}")
            sys.exit(1)
        
        logger.info(f"✓ Found tool: {tool.get('name', args.id)}")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool": tool
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print details
        logger.info("\n📋 Tool Details:")
        logger.info(f"  ID: {tool.get('id', 'N/A')}")
        logger.info(f"  Name: {tool.get('name', 'N/A')}")
        logger.info(f"  URL: {tool.get('url', 'N/A')}")
        logger.info(f"  Organization: {tool.get('organization', 'N/A')}")
        logger.info(f"  Description: {tool.get('description', 'N/A')}")
        logger.info(f"  Tool Class: {tool.get('toolclass', {}).get('name', 'N/A')}")
        
        versions = tool.get('versions', [])
        logger.info(f"  Versions: {len(versions)}")
        for v in versions[:5]:
            logger.info(f"    - {v.get('id', 'N/A')} ({v.get('name', 'N/A')})")
        if len(versions) > 5:
            logger.info(f"    ... and {len(versions) - 5} more")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_list_versions(args):
    """List all versions of a tool."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching versions for tool: {args.id}")
    
    try:
        trs = ToolRegistryService(args.registry)
        versions = trs.get_tool_versions(args.id)
        
        logger.info(f"✓ Found {len(versions)} versions")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool_id": args.id,
            "total_versions": len(versions),
            "versions": versions
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print versions
        logger.info("\n📋 Tool Versions:")
        for i, version in enumerate(versions, 1):
            v_id = version.get('id', 'N/A')
            v_name = version.get('name', 'N/A')
            is_prod = version.get('is_production', False)
            prod_marker = " [PRODUCTION]" if is_prod else ""
            logger.info(f"  {i}. {v_id} ({v_name}){prod_marker}")
            
            descriptors = version.get('descriptor_type', [])
            if descriptors:
                logger.info(f"     Descriptor Types: {', '.join(descriptors)}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_version(args):
    """Get a specific tool version."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    if not args.version:
        logger.error("❌ Version ID is required (use --version)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching version {args.version} of tool {args.id}")
    
    try:
        trs = ToolRegistryService(args.registry)
        version = trs.get_tool_version(args.id, args.version)
        
        if not version:
            logger.error(f"❌ Version not found: {args.version}")
            sys.exit(1)
        
        logger.info(f"✓ Found version: {version.get('name', args.version)}")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool_id": args.id,
            "version": version
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print details
        logger.info("\n📋 Version Details:")
        logger.info(f"  ID: {version.get('id', 'N/A')}")
        logger.info(f"  Name: {version.get('name', 'N/A')}")
        logger.info(f"  URL: {version.get('url', 'N/A')}")
        logger.info(f"  Production: {version.get('is_production', False)}")
        logger.info(f"  Verified: {version.get('verified', False)}")
        
        descriptors = version.get('descriptor_type', [])
        logger.info(f"  Descriptor Types: {', '.join(descriptors) if descriptors else 'N/A'}")
        
        images = version.get('images', [])
        if images:
            logger.info(f"  Container Images:")
            for img in images[:5]:
                logger.info(f"    - {img.get('image_name', 'N/A')}")
            if len(images) > 5:
                logger.info(f"    ... and {len(images) - 5} more")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_descriptor(args):
    """Get tool descriptor (CWL, WDL, etc.)."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    if not args.version:
        logger.error("❌ Version ID is required (use --version)")
        sys.exit(1)
    
    if not args.type:
        logger.error("❌ Descriptor type is required (use --type: CWL, WDL, NFL, GALAXY, SMK, etc.)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching {args.type} descriptor for {args.id} v{args.version}")
    
    try:
        trs = ToolRegistryService(args.registry)
        descriptor = trs.get_tool_descriptor(args.id, args.version, args.type)
        
        if not descriptor:
            logger.error(f"❌ Descriptor not found")
            sys.exit(1)
        
        logger.info(f"✓ Found descriptor")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool_id": args.id,
            "version": args.version,
            "descriptor_type": args.type,
            "descriptor": descriptor
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print content preview
        logger.info("\n📋 Descriptor Preview:")
        content = descriptor.get('content', '')[:500] if descriptor.get('content') else 'N/A'
        logger.info(content)
        if len(descriptor.get('content', '')) > 500:
            logger.info("... (truncated)")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_files(args):
    """Get list of files for a tool version."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    if not args.version:
        logger.error("❌ Version ID is required (use --version)")
        sys.exit(1)
    
    if not args.type:
        logger.error("❌ Descriptor type is required (use --type)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching files for {args.id} v{args.version} ({args.type})")
    
    try:
        trs = ToolRegistryService(args.registry)
        files = trs.get_tool_files(args.id, args.version, args.type)
        
        if isinstance(files, bytes):
            logger.info(f"✓ Retrieved zip file ({len(files)} bytes)")
            if args.output:
                with open(args.output, 'wb') as f:
                    f.write(files)
                logger.info(f"💾 Saved to {args.output}")
        else:
            logger.info(f"✓ Found {len(files)} files")
            
            output = {
                "timestamp": datetime.now().isoformat(),
                "registry_url": args.registry,
                "tool_id": args.id,
                "version": args.version,
                "descriptor_type": args.type,
                "total_files": len(files),
                "files": files
            }
            
            # Save to file if specified
            if args.output:
                save_output(output, args.output, args.format)
                logger.info(f"💾 Saved to {args.output}")
            
            # Print file list
            logger.info("\n📋 Files:")
            for i, file in enumerate(files[:20], 1):
                path = file.get('path', 'N/A')
                file_type = file.get('file_type', 'N/A')
                logger.info(f"  {i}. {path} ({file_type})")
            if len(files) > 20:
                logger.info(f"  ... and {len(files) - 20} more")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_tests(args):
    """Get test files for a tool version."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    if not args.id:
        logger.error("❌ Tool ID is required (use --id)")
        sys.exit(1)
    
    if not args.version:
        logger.error("❌ Version ID is required (use --version)")
        sys.exit(1)
    
    if not args.type:
        logger.error("❌ Descriptor type is required (use --type)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching test files for {args.id} v{args.version} ({args.type})")
    
    try:
        trs = ToolRegistryService(args.registry)
        tests = trs.get_tool_tests(args.id, args.version, args.type)
        
        logger.info(f"✓ Found {len(tests)} test files")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool_id": args.id,
            "version": args.version,
            "descriptor_type": args.type,
            "total_tests": len(tests),
            "tests": tests
        }
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print summary
        logger.info("\n📋 Test Files:")
        for i, test in enumerate(tests, 1):
            url = test.get('url', 'N/A')
            logger.info(f"  {i}. {url}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_list_classes(args):
    """List all tool classes."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching tool classes from {args.registry}...")
    
    try:
        trs = ToolRegistryService(args.registry)
        classes = trs.get_tool_classes()
        
        logger.info(f"✓ Found {len(classes)} tool classes")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "total_classes": len(classes),
            "tool_classes": classes
        }
        
        # Print JSON to stdout if requested
        if args.json:
            print_json_output(output)
            return output
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print classes
        logger.info("\n📋 Tool Classes:")
        for i, cls in enumerate(classes, 1):
            cls_id = cls.get('id', 'N/A')
            name = cls.get('name', 'N/A')
            description = cls.get('description', 'N/A')[:50]
            logger.info(f"  {i}. {cls_id}")
            logger.info(f"     Name: {name}")
            logger.info(f"     {description}...")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_service_info(args):
    """Get TRS service information."""
    logger = setup_logging(args.verbose)
    
    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)
    
    logger.info(f"🔍 Fetching service info from {args.registry}...")
    
    try:
        trs = ToolRegistryService(args.registry)
        info = trs.get_service_info()
        
        if not info:
            logger.error("❌ Could not retrieve service information")
            sys.exit(1)
        
        logger.info(f"✓ Retrieved service info")
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "service_info": info
        }
        
        # Print JSON to stdout if requested
        if args.json:
            print_json_output(output)
            return output
        
        # Save to file if specified
        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")
        
        # Print info
        logger.info("\n📋 Service Information:")
        logger.info(f"  ID: {info.get('id', 'N/A')}")
        logger.info(f"  Name: {info.get('name', 'N/A')}")
        logger.info(f"  Description: {info.get('description', 'N/A')}")
        logger.info(f"  Version: {info.get('version', 'N/A')}")
        
        org = info.get('organization', {})
        if org:
            logger.info(f"  Organization: {org.get('name', 'N/A')}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="fairbio-trs",
        description="Query GA4GH Tool Registry Service (TRS) endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  tools       List all tools (with optional filtering)
  tool        Get a specific tool by ID
  versions    List all versions of a tool
  version     Get a specific tool version
  descriptor  Get tool descriptor (CWL, WDL, etc.)
  files       Get file list for a tool version
  tests       Get test files for a tool version
  classes     List all tool classes
  info        Get TRS service information

Examples:
  fairbio-trs -r https://dockstore.org/api tools
  fairbio-trs -r https://dockstore.org/api tool --id quay.io/foo/bar
  fairbio-trs -r https://dockstore.org/api versions --id quay.io/foo/bar
  fairbio-trs -r https://dockstore.org/api version --id quay.io/foo/bar --version v1.0.0
  fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL
  fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL -o files.json
  fairbio-trs -r https://dockstore.org/api classes
  fairbio-trs info

Reference:
  https://github.com/ga4gh/tool-registry-service-schemas
        """
    )
    
    # Global options
    parser.add_argument(
        "-r", "--registry",
        metavar="URL",
        help="Base TRS registry API URL (required, must be specified before the subcommand) (e.g., https://dockstore.org)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="fairbio-trs 0.1.0"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Tools command
    tools_parser = subparsers.add_parser('tools', help='List tools')
    tools_parser.add_argument('--id', metavar='ID', help='Filter by tool ID')
    tools_parser.add_argument('--name', metavar='NAME', help='Filter by tool name')
    tools_parser.add_argument('--author', metavar='AUTHOR', help='Filter by author')
    tools_parser.add_argument('--description', metavar='DESC', help='Filter by description')
    tools_parser.add_argument('--descriptor-type', metavar='TYPE', 
                             help='Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)')
    tools_parser.add_argument('--limit', type=int, default=1000, help='Page size for each request (default: 1000)')
    tools_parser.add_argument('--all', action='store_true', help='Fetch ALL tools by automatically paginating through all results')
    tools_parser.add_argument('--offset', metavar='OFFSET', help='Start index for manual pagination (use --all to auto-paginate)')
    tools_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    tools_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                             help='Output format (default: json)')
    tools_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    tools_parser.set_defaults(func=cmd_list_tools)
    
    # Tool command
    tool_parser = subparsers.add_parser('tool', help='Get tool by ID')
    tool_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    tool_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    tool_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                            help='Output format (default: json)')
    tool_parser.set_defaults(func=cmd_get_tool)
    
    # Versions command
    versions_parser = subparsers.add_parser('versions', help='List tool versions')
    versions_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    versions_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    versions_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                               help='Output format (default: json)')
    versions_parser.set_defaults(func=cmd_list_versions)
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Get specific tool version')
    version_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    version_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    version_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    version_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                              help='Output format (default: json)')
    version_parser.set_defaults(func=cmd_get_version)
    
    # Descriptor command
    descriptor_parser = subparsers.add_parser('descriptor', help='Get tool descriptor')
    descriptor_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    descriptor_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    descriptor_parser.add_argument('--type', metavar='TYPE', required=True,
                                  help='Descriptor type (CWL, WDL, NFL, GALAXY, SMK)')
    descriptor_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    descriptor_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                 help='Output format (default: json)')
    descriptor_parser.set_defaults(func=cmd_get_descriptor)
    
    # Files command
    files_parser = subparsers.add_parser('files', help='Get tool files')
    files_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    files_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    files_parser.add_argument('--type', metavar='TYPE', required=True, help='Descriptor type')
    files_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    files_parser.add_argument('-f', '--format', choices=['json', 'text', 'zip'], default='json',
                            help='Output format (default: json)')
    files_parser.set_defaults(func=cmd_get_files)
    
    # Tests command
    tests_parser = subparsers.add_parser('tests', help='Get tool test files')
    tests_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    tests_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    tests_parser.add_argument('--type', metavar='TYPE', required=True, help='Descriptor type')
    tests_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    tests_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                            help='Output format (default: json)')
    tests_parser.set_defaults(func=cmd_get_tests)
    
    # Classes command
    classes_parser = subparsers.add_parser('classes', help='List tool classes')
    classes_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    classes_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                               help='Output format (default: json)')
    classes_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    classes_parser.set_defaults(func=cmd_list_classes)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get TRS service information')
    info_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    info_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                            help='Output format (default: json)')
    info_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    info_parser.set_defaults(func=cmd_service_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
