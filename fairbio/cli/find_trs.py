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
        if args.toolclass:
            filters['toolclass'] = args.toolclass

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

            pagination_info = {}
            if isinstance(tools, dict):
                tool_list = tools.get('tools', []) if 'tools' in tools else [tools] if tools else []
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

        # Apply local filtering for toolclass when provided
        if args.toolclass:
            lc = args.toolclass.lower()
            filtered = []
            for t in tool_list:
                tc = t.get('toolclass') or {}
                name = tc.get('name', '') if isinstance(tc, dict) else str(tc)
                if lc in name.lower():
                    filtered.append(t)
            tool_list = filtered
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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

        logger.info("\n📋 Tools Summary:")
        for i, tool in enumerate(tool_list[:10], 1):
            tool_id = tool.get('id', 'Unknown')
            name = tool.get('name', 'N/A')
            org = tool.get('organization', 'N/A')
            tc = tool.get('toolclass', {}).get('name', 'N/A') if isinstance(tool.get('toolclass'), dict) else tool.get('toolclass', 'N/A')
            logger.info(f"  {i}. {tool_id}")
            logger.info(f"     Name: {name}, Org: {org}, Class: {tc}")
        if total > 10:
            logger.info(f"  ... and {total - 10} more")

        if args.all:
            logger.info("\n📄 Pagination Summary:")
            logger.info(f"  Total Pages Retrieved: {pagination_info.get('total_pages')}")
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


def cmd_search_tools(args):
    """Search for tools using common filters (convenience command)."""
    logger = setup_logging(args.verbose)

    if not args.registry:
        logger.error("❌ Registry URL is required (use -r/--registry)")
        sys.exit(1)

    logger.info(f"🔍 Searching tools in {args.registry}...")

    try:
        trs = ToolRegistryService(args.registry)
        tool_list = trs.search_tools(
            query=args.query,
            descriptor_type=args.descriptor_type,
            author=args.author,
            limit=args.limit
        )

        total = len(tool_list)
        logger.info(f"✓ Found {total} tools")

        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "search": {
                "query": args.query,
                "descriptor_type": args.descriptor_type,
                "author": args.author,
                "limit": args.limit
            },
            "total_tools": total,
            "tools": tool_list
        }

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

        logger.info("\n📋 Search Results:")
        for i, tool in enumerate(tool_list[:10], 1):
            tool_id = tool.get('id', 'Unknown')
            name = tool.get('name', 'N/A')
            org = tool.get('organization', 'N/A')
            logger.info(f"  {i}. {tool_id}")
            logger.info(f"     Name: {name}, Org: {org}")
        if total > 10:
            logger.info(f"  ... and {total - 10} more")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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

        if args.path:
            logger.info(f"   Relative path: {args.path}")
            descriptor = trs.get_tool_descriptor_by_path(args.id, args.version, args.type, args.path)
        else:
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
            "relative_path": args.path if args.path else None,
            "descriptor": descriptor
        }

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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
        fmt = args.format if args.format == 'zip' else None
        files = trs.get_tool_files(args.id, args.version, args.type, format=fmt)

        if isinstance(files, bytes):
            logger.info(f"✓ Retrieved zip file ({len(files)} bytes)")
            if args.output:
                with open(args.output, 'wb') as f:
                    f.write(files)
                logger.info(f"💾 Saved to {args.output}")
            else:
                logger.info("ℹ️  Use -o/--output to save the zip file")
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

            if args.json:
                print_json_output(output)
                return output

            if args.output:
                save_output(output, args.output, args.format)
                logger.info(f"💾 Saved to {args.output}")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

        logger.info("\n📋 Test Files:")
        for i, test in enumerate(tests, 1):
            url = test.get('url', 'N/A')
            logger.info(f"  {i}. {url}")

        return output

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


def cmd_get_containerfile(args):
    """Get container specification(s) for a tool version (e.g., Dockerfiles)."""
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

    logger.info(f"🔍 Fetching containerfile(s) for {args.id} v{args.version}")

    try:
        trs = ToolRegistryService(args.registry)
        containerfiles = trs.get_tool_containerfile(args.id, args.version)

        logger.info(f"✓ Found {len(containerfiles)} containerfile(s)")

        output = {
            "timestamp": datetime.now().isoformat(),
            "registry_url": args.registry,
            "tool_id": args.id,
            "version": args.version,
            "total_containerfiles": len(containerfiles),
            "containerfiles": containerfiles
        }

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

        logger.info("\n📋 Containerfiles:")
        for i, cf in enumerate(containerfiles, 1):
            url = cf.get('url', 'N/A')
            content_preview = (cf.get('content', '') or '')[:200]
            logger.info(f"  {i}. URL: {url}")
            if content_preview:
                logger.info(f"     Preview: {content_preview}...")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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

        if args.json:
            print_json_output(output)
            return output

        if args.output:
            save_output(output, args.output, args.format)
            logger.info(f"💾 Saved to {args.output}")

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
  tools          List all tools (with optional filtering)
  search         Search tools by name, descriptor type, or author
  tool           Get a specific tool by ID
  versions       List all versions of a tool
  version        Get a specific tool version
  descriptor     Get tool descriptor (CWL, WDL, etc.); use --path for relative file
  files          Get file list for a tool version (use --format zip to download archive)
  tests          Get test files for a tool version
  containerfile  Get container specification(s) (Dockerfiles, Singularity recipes) for a version
  classes        List all tool classes
  info           Get TRS service information

Examples:
  fairbio-trs -r https://dockstore.org/api tools
  fairbio-trs -r https://dockstore.org/api tools --all
  fairbio-trs -r https://dockstore.org/api tools --descriptor-type CWL --toolclass Workflow
  fairbio-trs -r https://dockstore.org/api search --query samtools --descriptor-type CWL
  fairbio-trs -r https://dockstore.org/api tool --id quay.io/foo/bar
  fairbio-trs -r https://dockstore.org/api versions --id quay.io/foo/bar
  fairbio-trs -r https://dockstore.org/api version --id quay.io/foo/bar --version v1.0.0
  fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL
  fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type CWL --path tools/helper.cwl
  fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL -o files.json
  fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL --format zip -o bundle.zip
  fairbio-trs -r https://dockstore.org/api containerfile --id quay.io/foo/bar --version v1.0.0
  fairbio-trs -r https://dockstore.org/api classes
  fairbio-trs -r https://dockstore.org/api info

Reference:
  https://github.com/ga4gh/tool-registry-service-schemas
        """
    )

    # Global options
    parser.add_argument(
        "-r", "--registry",
        metavar="URL",
        help="Base TRS registry API URL (e.g., https://dockstore.org)"
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

    # ── tools ──────────────────────────────────────────────────────────────
    tools_parser = subparsers.add_parser('tools', help='List tools')
    tools_parser.add_argument('--id', metavar='ID', help='Filter by tool ID')
    tools_parser.add_argument('--name', metavar='NAME', help='Filter by tool name')
    tools_parser.add_argument('--author', metavar='AUTHOR', help='Filter by author')
    tools_parser.add_argument('--description', metavar='DESC', help='Filter by description')
    tools_parser.add_argument('--descriptor-type', metavar='TYPE',
                              help='Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)')
    tools_parser.add_argument('--toolclass', metavar='CLASS',
                              help='Filter by tool class name (e.g. CommandLineTool)')
    tools_parser.add_argument('--limit', type=int, default=1000,
                              help='Page size for each request (default: 1000)')
    tools_parser.add_argument('--all', action='store_true',
                              help='Fetch ALL tools by automatically paginating through all results')
    tools_parser.add_argument('--offset', metavar='OFFSET',
                              help='Start index for manual pagination')
    tools_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    tools_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                              help='Output format (default: json)')
    tools_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    tools_parser.set_defaults(func=cmd_list_tools)

    # ── search ─────────────────────────────────────────────────────────────
    search_parser = subparsers.add_parser('search', help='Search tools by name, type, or author')
    search_parser.add_argument('--query', metavar='QUERY', help='Search term (matches name/toolname)')
    search_parser.add_argument('--descriptor-type', metavar='TYPE',
                               help='Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)')
    search_parser.add_argument('--author', metavar='AUTHOR', help='Filter by author')
    search_parser.add_argument('--limit', type=int, default=1000,
                               help='Maximum number of results (default: 1000)')
    search_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    search_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                               help='Output format (default: json)')
    search_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    search_parser.set_defaults(func=cmd_search_tools)

    # ── tool ───────────────────────────────────────────────────────────────
    tool_parser = subparsers.add_parser('tool', help='Get tool by ID')
    tool_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    tool_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    tool_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                             help='Output format (default: json)')
    tool_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    tool_parser.set_defaults(func=cmd_get_tool)

    # ── versions ───────────────────────────────────────────────────────────
    versions_parser = subparsers.add_parser('versions', help='List tool versions')
    versions_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    versions_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    versions_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                 help='Output format (default: json)')
    versions_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    versions_parser.set_defaults(func=cmd_list_versions)

    # ── version ────────────────────────────────────────────────────────────
    version_parser = subparsers.add_parser('version', help='Get specific tool version')
    version_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    version_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    version_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    version_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                help='Output format (default: json)')
    version_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    version_parser.set_defaults(func=cmd_get_version)

    # ── descriptor ─────────────────────────────────────────────────────────
    descriptor_parser = subparsers.add_parser('descriptor', help='Get tool descriptor')
    descriptor_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    descriptor_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    descriptor_parser.add_argument('--type', metavar='TYPE', required=True,
                                   help='Descriptor type (CWL, WDL, NFL, GALAXY, SMK, PLAIN_CWL, PLAIN_WDL, etc.)')
    descriptor_parser.add_argument('--path', metavar='PATH',
                                   help='Relative path to a secondary descriptor file '
                                        '(maps to GET /tools/{id}/versions/{version}/{type}/descriptor/{relative_path})')
    descriptor_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    descriptor_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                   help='Output format (default: json)')
    descriptor_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    descriptor_parser.set_defaults(func=cmd_get_descriptor)

    # ── files ──────────────────────────────────────────────────────────────
    files_parser = subparsers.add_parser('files', help='Get tool files')
    files_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    files_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    files_parser.add_argument('--type', metavar='TYPE', required=True, help='Descriptor type')
    files_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    files_parser.add_argument('-f', '--format', choices=['json', 'text', 'zip'], default='json',
                              help='Output format — use "zip" to download all files as a zip archive (default: json)')
    files_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    files_parser.set_defaults(func=cmd_get_files)

    # ── tests ──────────────────────────────────────────────────────────────
    tests_parser = subparsers.add_parser('tests', help='Get tool test files')
    tests_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    tests_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    tests_parser.add_argument('--type', metavar='TYPE', required=True, help='Descriptor type')
    tests_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    tests_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                              help='Output format (default: json)')
    tests_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    tests_parser.set_defaults(func=cmd_get_tests)

    # ── containerfile ──────────────────────────────────────────────────────
    containerfile_parser = subparsers.add_parser(
        'containerfile',
        help='Get container specification(s) for a tool version (Dockerfiles, Singularity recipes, etc.)'
    )
    containerfile_parser.add_argument('--id', metavar='ID', required=True, help='Tool ID')
    containerfile_parser.add_argument('--version', metavar='VERSION', required=True, help='Version ID')
    containerfile_parser.add_argument('-o', '--output', metavar='FILE', help='Save to file')
    containerfile_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                      help='Output format (default: json)')
    containerfile_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    containerfile_parser.set_defaults(func=cmd_get_containerfile)

    # ── classes ────────────────────────────────────────────────────────────
    classes_parser = subparsers.add_parser('classes', help='List tool classes')
    classes_parser.add_argument('-o', '--output', metavar='FILE', help='Save results to file')
    classes_parser.add_argument('-f', '--format', choices=['json', 'text'], default='json',
                                help='Output format (default: json)')
    classes_parser.add_argument('--json', action='store_true', help='Print raw JSON to stdout')
    classes_parser.set_defaults(func=cmd_list_classes)

    # ── info ───────────────────────────────────────────────────────────────
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

    args.func(args)


if __name__ == "__main__":
    main()