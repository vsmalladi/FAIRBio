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
fairbio-ga4gh-registry -r https://custom-registry.org/ services
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

---

## Tool Registry Service (TRS) Query (`fairbio-trs`)

The `fairbio-trs` command provides direct access to GA4GH Tool Registry Service (TRS) endpoints, allowing you to discover and query tools, workflows, and their metadata.

Reference: https://github.com/ga4gh/tool-registry-service-schemas

### Commands

| Command | Description |
|---|---|
| `tools` | List all tools with optional filtering and pagination |
| `search` | Search tools by name, descriptor type, or author |
| `tool` | Get a specific tool by ID |
| `versions` | List all versions of a tool |
| `version` | Get a specific tool version |
| `descriptor` | Get a tool descriptor (CWL, WDL, etc.); use `--path` for secondary files |
| `files` | Get file list for a tool version; use `--format zip` to download an archive |
| `tests` | Get test parameter files for a tool version |
| `containerfile` | Get container specifications (Dockerfiles, Singularity recipes) for a version |
| `classes` | List all tool classes available in the registry |
| `info` | Get TRS service information |

### Global Options

| Option | Description |
|---|---|
| `-r, --registry URL` | TRS registry API base URL (required for all commands) |
| `-v, --verbose` | Enable verbose logging |
| `-h, --help` | Show help message |

### Basic Commands

```bash
# List tools
fairbio-trs -r https://dockstore.org/api tools

# Search tools
fairbio-trs -r https://dockstore.org/api search --query samtools

# Get a specific tool
fairbio-trs -r https://dockstore.org/api tool --id quay.io/foo/bar

# List all versions of a tool
fairbio-trs -r https://dockstore.org/api versions --id quay.io/foo/bar

# Get a specific tool version
fairbio-trs -r https://dockstore.org/api version --id quay.io/foo/bar --version v1.0.0

# Get a tool descriptor
fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL

# Get a secondary descriptor file by relative path
fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type CWL --path tools/helper.cwl

# Get file list for a tool version
fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL

# Download all files as a zip archive
fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL --format zip -o bundle.zip

# Get test parameter files
fairbio-trs -r https://dockstore.org/api tests --id quay.io/foo/bar --version v1.0.0 --type CWL

# Get container specifications (Dockerfiles, etc.)
fairbio-trs -r https://dockstore.org/api containerfile --id quay.io/foo/bar --version v1.0.0

# List all tool classes
fairbio-trs -r https://dockstore.org/api classes

# Get TRS service information
fairbio-trs -r https://dockstore.org/api info
```

### Per-Command Options

#### `tools` — List tools

```bash
fairbio-trs -r <URL> tools [options]
```

| Option | Description |
|---|---|
| `--id ID` | Filter by tool ID |
| `--name NAME` | Filter by tool name |
| `--author AUTHOR` | Filter by author |
| `--description DESC` | Filter by description keyword |
| `--descriptor-type TYPE` | Filter by descriptor type (`CWL`, `WDL`, `NFL`, `GALAXY`, `SMK`) |
| `--toolclass CLASS` | Filter by tool class name (e.g., `CommandLineTool`, `Workflow`) |
| `--limit N` | Page size per request (default: `1000`) |
| `--all` | Auto-paginate to fetch every page of results |
| `--offset N` | Start index for manual pagination |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `search` — Search tools

Convenience command that searches by name, descriptor type, and/or author in a single call.

```bash
fairbio-trs -r <URL> search [options]
```

| Option | Description |
|---|---|
| `--query QUERY` | Search term matched against tool name / toolname |
| `--descriptor-type TYPE` | Filter by descriptor type (`CWL`, `WDL`, `NFL`, `GALAXY`, `SMK`) |
| `--author AUTHOR` | Filter by author |
| `--limit N` | Maximum number of results (default: `1000`) |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `tool` — Get a specific tool

```bash
fairbio-trs -r <URL> tool --id ID [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `versions` — List all versions of a tool

```bash
fairbio-trs -r <URL> versions --id ID [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `version` — Get a specific tool version

```bash
fairbio-trs -r <URL> version --id ID --version VERSION [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `--version VERSION` | Version ID *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `descriptor` — Get a tool descriptor

Fetches the primary descriptor for a tool version. Use `--path` to retrieve a secondary/additional descriptor file by its relative path within the version.

```bash
fairbio-trs -r <URL> descriptor --id ID --version VERSION --type TYPE [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `--version VERSION` | Version ID *(required)* |
| `--type TYPE` | Descriptor type *(required)*: `CWL`, `WDL`, `NFL`, `GALAXY`, `SMK`, `PLAIN_CWL`, `PLAIN_WDL`, etc. |
| `--path PATH` | Relative path to a secondary descriptor file (e.g., `tools/helper.cwl`) |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `files` — Get file list for a tool version

```bash
fairbio-trs -r <URL> files --id ID --version VERSION --type TYPE [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `--version VERSION` | Version ID *(required)* |
| `--type TYPE` | Descriptor type *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default), `text`, or `zip` (downloads all files as an archive; requires `-o`) |
| `--json` | Print raw JSON to stdout |

#### `tests` — Get test parameter files

```bash
fairbio-trs -r <URL> tests --id ID --version VERSION --type TYPE [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `--version VERSION` | Version ID *(required)* |
| `--type TYPE` | Descriptor type *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `containerfile` — Get container specifications

Fetches Dockerfiles, Singularity recipes, or other container specifications for a tool version.

```bash
fairbio-trs -r <URL> containerfile --id ID --version VERSION [options]
```

| Option | Description |
|---|---|
| `--id ID` | Tool ID *(required)* |
| `--version VERSION` | Version ID *(required)* |
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `classes` — List tool classes

```bash
fairbio-trs -r <URL> classes [options]
```

| Option | Description |
|---|---|
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

#### `info` — Get TRS service information

```bash
fairbio-trs -r <URL> info [options]
```

| Option | Description |
|---|---|
| `-o, --output FILE` | Save results to file |
| `-f, --format` | Output format: `json` (default) or `text` |
| `--json` | Print raw JSON to stdout |

### Example Workflows

**Fetch all tools from a registry (auto-pagination):**
```bash
# Paginate automatically through all results
fairbio-trs -r https://dockstore.org/api tools --all -o all_tools.json

# All CommandLineTool tools
fairbio-trs -r https://dockstore.org/api tools --all --toolclass CommandLineTool -o cmdline_tools.json

# All WDL workflows
fairbio-trs -r https://dockstore.org/api tools --all --descriptor-type WDL --toolclass Workflow -o wdl_workflows.json

# Pipe total count to jq
fairbio-trs -r https://dockstore.org/api tools --all --json | jq '.total_tools'
```

**Search for tools:**
```bash
# Search by name
fairbio-trs -r https://dockstore.org/api search --query samtools

# Narrow to a specific descriptor type
fairbio-trs -r https://dockstore.org/api search --query samtools --descriptor-type CWL

# Search by author
fairbio-trs -r https://dockstore.org/api search --author "John Doe" -o results.json
```

**Manual pagination:**
```bash
# First page
fairbio-trs -r https://dockstore.org/api tools --limit 500 -o page1.json

# Next page
fairbio-trs -r https://dockstore.org/api tools --limit 500 --offset 500 -o page2.json
```

**Inspect a tool and its versions:**
```bash
fairbio-trs -r https://dockstore.org/api tool --id quay.io/foo/bar --json
fairbio-trs -r https://dockstore.org/api versions --id quay.io/foo/bar
fairbio-trs -r https://dockstore.org/api version --id quay.io/foo/bar --version v1.0.0
```

**Work with descriptors:**
```bash
# Primary WDL descriptor
fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type WDL -o workflow.wdl

# Secondary CWL file by relative path
fairbio-trs -r https://dockstore.org/api descriptor --id quay.io/foo/bar --version v1.0.0 --type CWL --path tools/helper.cwl -o helper.cwl
```

**Download files and test parameters:**
```bash
# List files as JSON
fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL -o files.json

# Download all files as a zip archive
fairbio-trs -r https://dockstore.org/api files --id quay.io/foo/bar --version v1.0.0 --type WDL --format zip -o bundle.zip

# Get test parameter files
fairbio-trs -r https://dockstore.org/api tests --id quay.io/foo/bar --version v1.0.0 --type CWL -o tests.json
```

**Get container specifications:**
```bash
fairbio-trs -r https://dockstore.org/api containerfile --id quay.io/foo/bar --version v1.0.0
fairbio-trs -r https://dockstore.org/api containerfile --id quay.io/foo/bar --version v1.0.0 -o containerfiles.json
```

**Discover registry metadata:**
```bash
# What tool classes does this registry support?
fairbio-trs -r https://dockstore.org/api classes

# Service info
fairbio-trs -r https://dockstore.org/api info --json | jq '.service_info.version'
```