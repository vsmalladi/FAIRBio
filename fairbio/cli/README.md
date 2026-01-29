# FAIRBio CLI Tools

This directory contains command-line tools for FAIRBio.

## GA4GH Service Registry Discovery (`fairbio-ga4gh-registry`)

The `fairbio-ga4gh-registry` command provides access to the GA4GH Service Registry, allowing you to discover and query GA4GH services including TRS (Tool Registry Service), WES, and other standardized services.

Reference: https://github.com/ga4gh-discovery/ga4gh-service-registry

### Basic Commands

```bash
# List all services in the registry
fairbio-ga4gh-registry services

# List services of a specific type (e.g., TRS)
fairbio-ga4gh-registry services --type trs

# Save services to a file
fairbio-ga4gh-registry services --type trs -o trs_services.json

# Get a specific service by ID
fairbio-ga4gh-registry service --id org.dockstore.dockstoreapi

# List all available service types
fairbio-ga4gh-registry types

# Get registry information
fairbio-ga4gh-registry info

# Use text format output instead of JSON
fairbio-ga4gh-registry services --type wes -f text -o wes_services.txt

# Verbose logging
fairbio-ga4gh-registry services -v

# Use custom registry URL
fairbio-ga4gh-registry services -r https://custom-registry.org/
```

### Available Options

- `-t, --type` - Filter services by type (e.g., `trs`, `wes`, `tes`, `drs`)
- `-o, --output` - Save results to a file (JSON or text format)
- `-f, --format` - Output format: `json` (default) or `text`
- `-i, --id` - Service ID to retrieve
- `-r, --registry` - Custom GA4GH Service Registry URL
- `-v, --verbose` - Enable verbose logging
- `-h, --help` - Show help message

### Example Workflows

**Discover all TRS registries and save to file:**
```bash
fairbio-ga4gh-registry services --type trs -o my_trs_registries.json
```

**Get details about a specific service:**
```bash
fairbio-ga4gh-registry service --id org.dockstore.dockstoreapi -o dockstore_info.json
```

**List service types in text format:**
```bash
fairbio-ga4gh-registry types -f text -o service_types.txt
```

## Tool Registry Service (TRS) Query (`fairbio-trs`)

The `fairbio-trs` command provides direct access to GA4GH Tool Registry Service (TRS) endpoints, allowing you to discover and query tools, workflows, and their metadata.

Reference: https://github.com/ga4gh/tool-registry-service-schemas

### Basic Commands

```bash
# List all tools in a TRS registry
fairbio-trs -r https://dockstore.org/api tools

# Get a specific tool by ID
fairbio-trs -r https://dockstore.org/api tool --id quay.io/foo/bar

# List all versions of a tool
fairbio-trs -r https://dockstore.org/api versions --id quay.io/foo/bar

# Get a specific tool version
fairbio-trs -r https://dockstore.org/api version --id quay.io/foo/bar --version v1.0.0

# Get tool descriptor (CWL, WDL, etc.)
fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL

# Get file list for a tool version
fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL -o files.json

# Get test files for a tool
fairbio-trs -r https://dockstore.org/api tests --id quay.io/foo/bar --version v1.0.0 --type WDL

# List all tool classes
fairbio-trs -r https://dockstore.org/api classes

# Get TRS service information
fairbio-trs -r https://dockstore.org/api info

# Verbose logging
fairbio-trs -v -r https://dockstore.org/api tools
```

### Available Options

**Global options:**
- `-r, --registry` - TRS registry URL (required for most commands)
- `-v, --verbose` - Enable verbose logging
- `-o, --output` - Save results to a file
- `-f, --format` - Output format: `json` (default) or `text`
- `--json` - Print raw JSON to stdout (for `tools`, `classes`, `info` commands)
- `-h, --help` - Show help message

**Filtering options (tools command):**
- `--id` - Filter by tool ID
- `--name` - Filter by tool name
- `--author` - Filter by tool author
- `--description` - Filter by tool description
- `--descriptor-type` - Filter by descriptor type (CWL, WDL, NFL, GALAXY, SMK)
- `--limit` - Page size for each request (default: 1000)
- `--all` - **Automatically fetch ALL tools by paginating through all results**
- `--offset` - Start index for manual pagination (use `--all` for automatic pagination)

**Version/Descriptor options:**
- `--id` - Tool ID (required)
- `--version` - Version ID (required for version, descriptor, files, tests commands)
- `--type` - Descriptor type: CWL, WDL, NFL, GALAXY, SMK, PLAIN_CWL, PLAIN_WDL, etc.

### Example Workflows

**Fetch all tools from a registry (auto-pagination):**
```bash
# Automatically paginate through all results
fairbio-trs tools --all -o all_tools.json

# Get all tools with filters
fairbio-trs tools --all --descriptor-type WDL -o all_wdl_tools.json

# Get all tools as JSON to stdout for piping
fairbio-trs tools --all --json | jq '.total_tools'
```

**Manual pagination through results:**
```bash
# Get first page of 500 tools
fairbio-trs tools --limit 500 -o page1.json

# Get next page using offset from response
fairbio-trs tools --limit 500 --offset "500" -o page2.json
```

**Search for tools in Dockstore:**
```bash
fairbio-trs tools --name "samtools" -o samtools_tools.json
```

**Get a workflow descriptor:**
```bash
fairbio-trs descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL -o workflow.wdl
```

**Download all files for a tool version:**
```bash
fairbio-trs files --id quay.io/foo/bar --version v1.0.0 --type WDL -f zip -o tool_files.zip
```

**Get test parameters for a CWL tool:**
```bash
fairbio-trs tests --id quay.io/foo/bar --version v1.0.0 --type CWL -o tests.json
```

**Get pagination information:**
```bash
# View pagination details in JSON output
fairbio-trs tools --json | jq '.pagination'

# Shows: current_offset, current_limit, next_page, last_page, self_link
```
