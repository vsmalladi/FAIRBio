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
