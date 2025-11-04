#!/bin/bash

# Script to create all GitHub issues for HF Dataset Integration
# Run this script after reviewing the issue descriptions in HF_DATASET_GITHUB_ISSUES.md

set -e

REPO="davanstrien/embedding-atlas"

echo "Creating GitHub issues for HF Dataset Integration..."
echo "Repository: $REPO"
echo ""

# Issue #1: Add Hugging Face dataset export functionality
gh issue create \
  --repo "$REPO" \
  --title "Add Hugging Face dataset export functionality" \
  --label "enhancement,backend,priority-high,sprint-1" \
  --body "$(cat <<'EOF'
### Description
Add capability to export Embedding Atlas data to Hugging Face datasets, enabling remote storage and sharing of atlas visualizations.

### Background
Currently, Embedding Atlas stores data locally as parquet files. By supporting export to HF datasets, users can:
- Share atlases publicly or privately
- Deploy static viewers without backend infrastructure
- Leverage HF's CDN for data delivery
- Version control their atlas data

### Tasks
- [ ] Add `push_to_hub()` method to `DataSource` class
- [ ] Export parquet file with all required columns (projection_x, projection_y, __neighbors, etc.)
- [ ] Include metadata.json as a dataset file
- [ ] Handle HF authentication (tokens)
- [ ] Add optional README.md generation with dataset card
- [ ] Add proper error handling for network issues

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/data_source.py\`
- \`packages/backend/embedding_atlas/cli.py\`

**Dependencies:**
- \`huggingface_hub\` Python package

### Acceptance Criteria
- [ ] Can export complete atlas to HF dataset
- [ ] Metadata is preserved in the dataset
- [ ] Dataset is accessible via HF web interface
- [ ] Works with both public and private datasets
- [ ] Authentication errors are clear and actionable
- [ ] Includes tests with mocked HF API

### Example API
\`\`\`python
from embedding_atlas import DataSource

ds = DataSource(identifier="my-atlas", dataset=df, metadata=metadata)
ds.push_to_hub("username/my-atlas", private=False, token="hf_...")
\`\`\`
EOF
)"

echo "✓ Created Issue #1: Add Hugging Face dataset export functionality"

# Issue #2: Add CLI command for HF dataset export
gh issue create \
  --repo "$REPO" \
  --title "Add CLI command for HF dataset export" \
  --label "enhancement,backend,CLI,priority-high,sprint-1" \
  --body "$(cat <<'EOF'
### Description
Add \`embedding-atlas export-hf\` CLI command to export existing atlas to Hugging Face datasets.

### Dependencies
- Requires Issue #1 to be completed

### Tasks
- [ ] Add \`export-hf\` subcommand to CLI
- [ ] Add flags: \`--repo-id\`, \`--private\`, \`--token\`, \`--commit-message\`
- [ ] Provide helpful error messages for authentication issues
- [ ] Add progress reporting for upload
- [ ] Support reading token from environment variable
- [ ] Add dry-run mode to preview upload

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/cli.py\`

### Acceptance Criteria
- [ ] Command successfully exports to HF
- [ ] Clear error messages for common issues (auth, network, etc.)
- [ ] Progress indication during upload
- [ ] Help documentation is clear
- [ ] Works with existing atlas files

### Example Usage
\`\`\`bash
# Basic export
embedding-atlas export-hf my-data.parquet --repo-id username/my-atlas

# Private dataset with token
embedding-atlas export-hf my-data.parquet \
  --repo-id username/my-atlas \
  --private \
  --token $HF_TOKEN

# With custom commit message
embedding-atlas export-hf my-data.parquet \
  --repo-id username/my-atlas \
  --commit-message "Updated embeddings"
\`\`\`
EOF
)"

echo "✓ Created Issue #2: Add CLI command for HF dataset export"

# Issue #3: Add CLI command to create atlas from HF dataset
gh issue create \
  --repo "$REPO" \
  --title "Add CLI command to create atlas from HF dataset" \
  --label "enhancement,backend,CLI,priority-medium,sprint-2" \
  --body "$(cat <<'EOF'
### Description
Add \`embedding-atlas from-hf\` CLI command to load and visualize HF datasets directly.

### Tasks
- [ ] Add \`from-hf\` subcommand to CLI
- [ ] Support \`hf://\` URLs and repo IDs
- [ ] Auto-detect columns if using standard naming convention
- [ ] Allow column mapping via flags (--id, --text, --x, --y)
- [ ] Download and cache dataset locally
- [ ] Launch viewer after loading

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/cli.py\`
- \`packages/backend/embedding_atlas/utils.py\`

### Acceptance Criteria
- [ ] Can load atlas from HF dataset URL or repo ID
- [ ] Works with various HF dataset formats
- [ ] Respects local caching
- [ ] Clear error messages for missing columns
- [ ] Viewer launches successfully

### Example Usage
\`\`\`bash
# Load from repo ID
embedding-atlas from-hf username/my-atlas

# Load from hf:// URL
embedding-atlas from-hf hf://datasets/username/my-atlas

# With column mapping
embedding-atlas from-hf username/my-atlas \
  --x projection_x \
  --y projection_y \
  --text description
\`\`\`
EOF
)"

echo "✓ Created Issue #3: Add CLI command to create atlas from HF dataset"

# Issue #4: Update data loading to support HF URLs
gh issue create \
  --repo "$REPO" \
  --title "Update data loading to support HF URLs" \
  --label "enhancement,backend,priority-medium,sprint-2" \
  --body "$(cat <<'EOF'
### Description
Extend the existing data loading infrastructure to accept \`hf://\` URLs and HF repo IDs as data sources in all commands.

### Tasks
- [ ] Detect HF URLs in data path argument
- [ ] Use \`datasets.load_dataset()\` for HF sources
- [ ] Handle authentication for private datasets
- [ ] Add caching behavior
- [ ] Update all CLI commands to work with HF URLs

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/utils.py\` (in \`determine_and_load_data()\`)

### Acceptance Criteria
- [ ] Can pass HF URLs to existing commands (e.g., \`embedding-atlas hf://...\`)
- [ ] Works seamlessly with current API
- [ ] Backward compatible with file paths
- [ ] Proper error handling

### Example Usage
\`\`\`bash
# Works with existing commands
embedding-atlas hf://datasets/username/my-atlas
embedding-atlas serve hf://datasets/username/my-atlas
\`\`\`
EOF
)"

echo "✓ Created Issue #4: Update data loading to support HF URLs"

# Issue #5: Support remote dataset URLs in viewer metadata
gh issue create \
  --repo "$REPO" \
  --title "Support remote dataset URLs in viewer metadata" \
  --label "enhancement,frontend,priority-high,sprint-1" \
  --body "$(cat <<'EOF'
### Description
Update \`BackendDataSource\` to support loading parquet files from arbitrary HTTP(S) and \`hf://\` URLs.

### Background
Currently, the viewer loads parquet from relative URLs (e.g., \`./data/dataset.parquet\`). To support HF-hosted datasets, we need to:
- Accept full URLs in metadata
- Load data from remote sources via DuckDB
- Handle CORS and network errors gracefully

### Tasks
- [ ] Extend \`Metadata\` interface to support \`datasetUrl\` field
- [ ] Modify initialization to use custom URL if provided
- [ ] Handle both absolute and relative URLs
- [ ] Add error handling for CORS issues
- [ ] Test with HF dataset URLs
- [ ] Update TypeScript types

### Technical Details
**Files to modify:**
- \`packages/viewer/src/app/backend_data_source.ts\`
- \`packages/viewer/src/app/data_source.ts\` (interface)

### Acceptance Criteria
- [ ] Can load parquet from HF URLs
- [ ] Works with \`hf://\` protocol
- [ ] Clear error messages for network issues
- [ ] Maintains compatibility with local URLs
- [ ] TypeScript types are accurate

### Example metadata.json
\`\`\`json
{
  "props": {
    "data": {
      "table": "atlas",
      "id": "_row_index",
      "text": "description",
      "projection": {"x": "projection_x", "y": "projection_y"}
    }
  },
  "database": {
    "type": "wasm",
    "load": true,
    "datasetUrl": "hf://datasets/username/my-atlas@~parquet/**/*.parquet"
  }
}
\`\`\`
EOF
)"

echo "✓ Created Issue #5: Support remote dataset URLs in viewer metadata"

# Issue #6: Add DuckDB httpfs extension support
gh issue create \
  --repo "$REPO" \
  --title "Add DuckDB httpfs extension support" \
  --label "enhancement,frontend,priority-high,sprint-1" \
  --body "$(cat <<'EOF'
### Description
Ensure DuckDB WASM has the httpfs extension properly installed and configured for remote file access.

### Background
DuckDB requires the httpfs extension to read remote parquet files. Need to:
- Verify extension availability in current build
- Configure for browser compatibility
- Support \`hf://\` URLs

### Tasks
- [ ] Check if httpfs is included in current DuckDB WASM build
- [ ] Add httpfs installation/loading if needed
- [ ] Configure HTTP settings for browser compatibility
- [ ] Test with various remote parquet sources (HF, direct URLs)
- [ ] Add retry logic for network failures
- [ ] Handle authentication if needed

### Technical Details
**Files to modify:**
- \`packages/viewer/src/utils/duckdb.ts\`
- \`packages/viewer/src/utils/database.ts\`

**Current relevant code:**
\`\`\`typescript
// duckdb.ts:54 - currently forces full HTTP reads
await db.open({
  filesystem: {
    forceFullHTTPReads: true,
  },
});
\`\`\`

### Acceptance Criteria
- [ ] Can read remote parquet via HTTP(S)
- [ ] \`hf://\` URLs work correctly
- [ ] Handles network errors gracefully
- [ ] Works in all supported browsers (Chrome, Firefox, Safari, Edge)
- [ ] Performance is acceptable

### Testing
- Test with small (<1MB) and large (>100MB) files
- Test network failure scenarios
- Test across different browsers
EOF
)"

echo "✓ Created Issue #6: Add DuckDB httpfs extension support"

# Issue #7: Create static viewer template
gh issue create \
  --repo "$REPO" \
  --title "Create static viewer template" \
  --label "enhancement,frontend,documentation,priority-medium,sprint-2" \
  --body "$(cat <<'EOF'
### Description
Create a minimal HTML template for deploying static atlas viewers that load data from HF datasets.

### Background
Users should be able to deploy viewers to GitHub Pages, Netlify, HF Spaces, etc. without backend infrastructure.

### Tasks
- [ ] Create \`static-viewer-template.html\`
- [ ] Include CDN links for embedding-atlas
- [ ] Document metadata.json structure
- [ ] Add example deployment instructions
- [ ] Support customization options (title, theme, initial state)
- [ ] Add browser compatibility checks

### Technical Details
**Files to create:**
- \`packages/viewer/static-viewer-template.html\`
- \`packages/docs/guides/static-viewer-deployment.md\`

### Acceptance Criteria
- [ ] Single-file HTML that works standalone
- [ ] Can be deployed to static hosting
- [ ] Clear customization instructions
- [ ] Includes fallback for unsupported browsers
- [ ] Works offline after initial load (with service worker)
EOF
)"

echo "✓ Created Issue #7: Create static viewer template"

# Issue #8: Add remote cache support
gh issue create \
  --repo "$REPO" \
  --title "Add remote cache support" \
  --label "enhancement,frontend,priority-low,sprint-4" \
  --body "$(cat <<'EOF'
### Description
Support loading cached data (labels, clusters, etc.) from remote URLs alongside the dataset.

### Dependencies
- Requires Issue #5

### Background
Pre-computed cache (labels, density clusters) can be stored in the HF dataset to speed up viewer initialization.

### Tasks
- [ ] Extend cache interface to support remote URLs
- [ ] Load cache files from HF dataset if available
- [ ] Fall back to generating cache if not found
- [ ] Store generated cache in browser IndexedDB
- [ ] Add cache versioning

### Technical Details
**Files to modify:**
- \`packages/viewer/src/app/backend_data_source.ts\`
- Cache structure in HF dataset: \`cache/*.json\`

### Acceptance Criteria
- [ ] Can load pre-computed cache from HF
- [ ] Graceful fallback if cache unavailable
- [ ] Browser storage caching works
- [ ] Cache version mismatches handled properly
EOF
)"

echo "✓ Created Issue #8: Add remote cache support"

# Issue #9: Add generate-static-viewer CLI command
gh issue create \
  --repo "$REPO" \
  --title "Add generate-static-viewer CLI command" \
  --label "enhancement,backend,CLI,priority-medium,sprint-2" \
  --body "$(cat <<'EOF'
### Description
Generate a complete static viewer package (HTML + metadata) from an atlas, ready for deployment.

### Dependencies
- Requires Issue #7

### Tasks
- [ ] Add \`generate-static-viewer\` subcommand to CLI
- [ ] Copy static viewer template
- [ ] Generate metadata.json with correct URLs
- [ ] Optionally include parquet file locally
- [ ] Create deployment README
- [ ] Support both HF dataset and local parquet sources
- [ ] Add options for customization (title, theme, etc.)

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/cli.py\`

### Acceptance Criteria
- [ ] Generates complete deployable package
- [ ] Works with both HF and local sources
- [ ] Includes deployment documentation
- [ ] Can customize viewer settings
- [ ] Output is ready for deployment
EOF
)"

echo "✓ Created Issue #9: Add generate-static-viewer CLI command"

# Issue #10: Add HF dataset validation command
gh issue create \
  --repo "$REPO" \
  --title "Add HF dataset validation command" \
  --label "enhancement,backend,CLI,priority-low,sprint-3" \
  --body "$(cat <<'EOF'
### Description
Validate that an HF dataset has the correct structure and columns for use with Embedding Atlas.

### Dependencies
- Requires Issue #1

### Tasks
- [ ] Add \`validate-hf-dataset\` subcommand to CLI
- [ ] Check for required columns (projection_x, projection_y)
- [ ] Validate data types
- [ ] Check metadata.json if present
- [ ] Provide helpful fix suggestions
- [ ] Validate __neighbors column format

### Technical Details
**Files to modify:**
- \`packages/backend/embedding_atlas/cli.py\`

**Files to create:**
- \`packages/backend/embedding_atlas/validation.py\`

### Acceptance Criteria
- [ ] Identifies missing/incorrect columns
- [ ] Suggests fixes for common issues
- [ ] Works with remote datasets
- [ ] Clear error messages
- [ ] Exit codes indicate success/failure
EOF
)"

echo "✓ Created Issue #10: Add HF dataset validation command"

# Issue #11: Write HF dataset workflow documentation
gh issue create \
  --repo "$REPO" \
  --title "Write HF dataset workflow documentation" \
  --label "documentation,priority-high,sprint-1" \
  --body "$(cat <<'EOF'
### Description
Create comprehensive documentation for the Hugging Face dataset workflow.

### Dependencies
- Should be written alongside Issues #1-#10 as they're implemented

### Tasks
- [ ] Create "Working with Hugging Face Datasets" guide
- [ ] Document export workflow
- [ ] Document static viewer deployment
- [ ] Add troubleshooting section
- [ ] Include architecture diagrams
- [ ] Add best practices (file size, chunking, private vs public)
- [ ] Document authentication setup
- [ ] Add performance considerations

### Technical Details
**Files to create:**
- \`packages/docs/guides/huggingface-datasets.md\`
- \`packages/docs/guides/static-viewer-deployment.md\`
- \`packages/docs/guides/troubleshooting-remote-loading.md\`

### Sections to Include
1. Overview & Benefits
2. Exporting Atlas to HF
3. Loading from HF in Python
4. Creating Static Viewers
5. Deployment Options (GitHub Pages, Netlify, HF Spaces)
6. Performance Optimization
7. Security & Privacy
8. Troubleshooting

### Acceptance Criteria
- [ ] Complete end-to-end workflow documented
- [ ] Covers common use cases
- [ ] Includes troubleshooting guide
- [ ] Has working code examples
- [ ] Diagrams explain architecture
EOF
)"

echo "✓ Created Issue #11: Write HF dataset workflow documentation"

# Issue #12: Create end-to-end HF workflow example
gh issue create \
  --repo "$REPO" \
  --title "Create end-to-end HF workflow example" \
  --label "documentation,example,priority-high,sprint-2" \
  --body "$(cat <<'EOF'
### Description
Create a complete working example demonstrating the entire HF dataset workflow from data to deployed viewer.

### Dependencies
- Requires Issues #1-#10 to be complete

### Tasks
- [ ] Create example Python script for data preparation
- [ ] Use a public dataset (e.g., wine reviews, papers, tweets)
- [ ] Generate embeddings and projections
- [ ] Export to HF dataset
- [ ] Generate static viewer
- [ ] Deploy to GitHub Pages or HF Spaces
- [ ] Document all steps in README
- [ ] Add video walkthrough

### Technical Details
**Files to create:**
- \`packages/examples/huggingface_workflow/\`
  - \`prepare_data.py\` - Load and prepare data
  - \`export_to_hf.py\` - Export to HF
  - \`generate_viewer.sh\` - Generate static viewer
  - \`README.md\` - Complete documentation
  - \`requirements.txt\` - Python dependencies
  - \`viewer/\` - Generated viewer files

### Acceptance Criteria
- [ ] Complete working example
- [ ] Reproducible steps
- [ ] Deployed demo available
- [ ] Well-documented with explanations
- [ ] Uses realistic dataset
EOF
)"

echo "✓ Created Issue #12: Create end-to-end HF workflow example"

# Issue #13-21 (Sprint 3 & 4)
echo ""
echo "Creating remaining issues for Sprint 3 & 4..."

gh issue create \
  --repo "$REPO" \
  --title "Add HF dataset examples to docs site" \
  --label "documentation,example,priority-medium,sprint-3" \
  --body "Add interactive examples using HF datasets to the Embedding Atlas documentation site. Requires Issue #12."

gh issue create \
  --repo "$REPO" \
  --title "Add backend tests for HF integration" \
  --label "testing,backend,priority-medium,sprint-3" \
  --body "Comprehensive test coverage for HF dataset functionality in the Python backend. Requires Issues #1-#4."

gh issue create \
  --repo "$REPO" \
  --title "Add frontend tests for remote loading" \
  --label "testing,frontend,priority-medium,sprint-3" \
  --body "Test suite for remote dataset loading in the viewer. Requires Issues #5-#8."

gh issue create \
  --repo "$REPO" \
  --title "Browser compatibility testing" \
  --label "testing,frontend,priority-low,sprint-3" \
  --body "Comprehensive browser compatibility testing for HF dataset loading. Requires Issues #5-#8."

gh issue create \
  --repo "$REPO" \
  --title "Add progress indicators for remote loading" \
  --label "enhancement,frontend,UX,priority-medium,sprint-3" \
  --body "Show loading progress when fetching remote parquet files. Requires Issue #5."

gh issue create \
  --repo "$REPO" \
  --title "Implement chunked loading for large datasets" \
  --label "enhancement,performance,priority-low,future" \
  --body "Support loading large datasets in chunks for better performance. Requires Issue #5."

gh issue create \
  --repo "$REPO" \
  --title "Optimize HTTP range request support" \
  --label "enhancement,performance,priority-low,future" \
  --body "Optimize loading by using HTTP range requests. Requires Issue #5."

gh issue create \
  --repo "$REPO" \
  --title "Update TypeScript types for HF metadata" \
  --label "enhancement,frontend,TypeScript,priority-low,sprint-4" \
  --body "Update TypeScript interfaces to reflect new metadata structure. Requires Issue #5."

gh issue create \
  --repo "$REPO" \
  --title "Improve CLI help and documentation" \
  --label "enhancement,CLI,documentation,priority-low,sprint-4" \
  --body "Enhance CLI help text for HF-related commands. Requires Issues #2, #3, #9."

echo ""
echo "✓ All GitHub issues created successfully!"
echo ""
echo "Next steps:"
echo "1. Review issues at: https://github.com/$REPO/issues"
echo "2. Add them to project board if using one"
echo "3. Start implementation with Sprint 1 issues (#1, #2, #5, #6, #11)"
