# GitHub Issues: Hugging Face Dataset Integration

This document contains formatted GitHub issues ready to be created. Each issue can be copied and pasted directly into GitHub.

---

## Issue #1: Add Hugging Face dataset export functionality

**Labels:** `enhancement`, `backend`, `priority-high`

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
- `packages/backend/embedding_atlas/data_source.py`
- `packages/backend/embedding_atlas/cli.py`

**Dependencies:**
- `huggingface_hub` Python package

### Acceptance Criteria
- [ ] Can export complete atlas to HF dataset
- [ ] Metadata is preserved in the dataset
- [ ] Dataset is accessible via HF web interface
- [ ] Works with both public and private datasets
- [ ] Authentication errors are clear and actionable
- [ ] Includes tests with mocked HF API

### Example API
```python
from embedding_atlas import DataSource

ds = DataSource(identifier="my-atlas", dataset=df, metadata=metadata)
ds.push_to_hub("username/my-atlas", private=False, token="hf_...")
```

---

## Issue #2: Add CLI command for HF dataset export

**Labels:** `enhancement`, `backend`, `CLI`, `priority-high`

### Description
Add `embedding-atlas export-hf` CLI command to export existing atlas to Hugging Face datasets.

### Dependencies
- Requires Issue #1 to be completed

### Tasks
- [ ] Add `export-hf` subcommand to CLI
- [ ] Add flags: `--repo-id`, `--private`, `--token`, `--commit-message`
- [ ] Provide helpful error messages for authentication issues
- [ ] Add progress reporting for upload
- [ ] Support reading token from environment variable
- [ ] Add dry-run mode to preview upload

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

### Acceptance Criteria
- [ ] Command successfully exports to HF
- [ ] Clear error messages for common issues (auth, network, etc.)
- [ ] Progress indication during upload
- [ ] Help documentation is clear
- [ ] Works with existing atlas files

### Example Usage
```bash
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
```

---

## Issue #3: Add CLI command to create atlas from HF dataset

**Labels:** `enhancement`, `backend`, `CLI`, `priority-medium`

### Description
Add `embedding-atlas from-hf` CLI command to load and visualize HF datasets directly.

### Tasks
- [ ] Add `from-hf` subcommand to CLI
- [ ] Support `hf://` URLs and repo IDs
- [ ] Auto-detect columns if using standard naming convention
- [ ] Allow column mapping via flags (--id, --text, --x, --y)
- [ ] Download and cache dataset locally
- [ ] Launch viewer after loading

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`
- `packages/backend/embedding_atlas/utils.py`

### Acceptance Criteria
- [ ] Can load atlas from HF dataset URL or repo ID
- [ ] Works with various HF dataset formats
- [ ] Respects local caching
- [ ] Clear error messages for missing columns
- [ ] Viewer launches successfully

### Example Usage
```bash
# Load from repo ID
embedding-atlas from-hf username/my-atlas

# Load from hf:// URL
embedding-atlas from-hf hf://datasets/username/my-atlas

# With column mapping
embedding-atlas from-hf username/my-atlas \
  --x projection_x \
  --y projection_y \
  --text description
```

---

## Issue #4: Update data loading to support HF URLs

**Labels:** `enhancement`, `backend`, `priority-medium`

### Description
Extend the existing data loading infrastructure to accept `hf://` URLs and HF repo IDs as data sources in all commands.

### Tasks
- [ ] Detect HF URLs in data path argument
- [ ] Use `datasets.load_dataset()` for HF sources
- [ ] Handle authentication for private datasets
- [ ] Add caching behavior
- [ ] Update all CLI commands to work with HF URLs

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/utils.py` (in `determine_and_load_data()`)

### Acceptance Criteria
- [ ] Can pass HF URLs to existing commands (e.g., `embedding-atlas hf://...`)
- [ ] Works seamlessly with current API
- [ ] Backward compatible with file paths
- [ ] Proper error handling

### Example Usage
```bash
# Works with existing commands
embedding-atlas hf://datasets/username/my-atlas
embedding-atlas serve hf://datasets/username/my-atlas
```

---

## Issue #5: Support remote dataset URLs in viewer metadata

**Labels:** `enhancement`, `frontend`, `priority-high`

### Description
Update `BackendDataSource` to support loading parquet files from arbitrary HTTP(S) and `hf://` URLs.

### Background
Currently, the viewer loads parquet from relative URLs (e.g., `./data/dataset.parquet`). To support HF-hosted datasets, we need to:
- Accept full URLs in metadata
- Load data from remote sources via DuckDB
- Handle CORS and network errors gracefully

### Tasks
- [ ] Extend `Metadata` interface to support `datasetUrl` field
- [ ] Modify initialization to use custom URL if provided
- [ ] Handle both absolute and relative URLs
- [ ] Add error handling for CORS issues
- [ ] Test with HF dataset URLs
- [ ] Update TypeScript types

### Technical Details
**Files to modify:**
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/app/data_source.ts` (interface)

### Acceptance Criteria
- [ ] Can load parquet from HF URLs
- [ ] Works with `hf://` protocol
- [ ] Clear error messages for network issues
- [ ] Maintains compatibility with local URLs
- [ ] TypeScript types are accurate

### Example metadata.json
```json
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
```

---

## Issue #6: Add DuckDB httpfs extension support

**Labels:** `enhancement`, `frontend`, `priority-high`

### Description
Ensure DuckDB WASM has the httpfs extension properly installed and configured for remote file access.

### Background
DuckDB requires the httpfs extension to read remote parquet files. Need to:
- Verify extension availability in current build
- Configure for browser compatibility
- Support `hf://` URLs

### Tasks
- [ ] Check if httpfs is included in current DuckDB WASM build
- [ ] Add httpfs installation/loading if needed
- [ ] Configure HTTP settings for browser compatibility
- [ ] Test with various remote parquet sources (HF, direct URLs)
- [ ] Add retry logic for network failures
- [ ] Handle authentication if needed

### Technical Details
**Files to modify:**
- `packages/viewer/src/utils/duckdb.ts`
- `packages/viewer/src/utils/database.ts`

**Current relevant code:**
```typescript
// duckdb.ts:54 - currently forces full HTTP reads
await db.open({
  filesystem: {
    forceFullHTTPReads: true,
  },
});
```

### Acceptance Criteria
- [ ] Can read remote parquet via HTTP(S)
- [ ] `hf://` URLs work correctly
- [ ] Handles network errors gracefully
- [ ] Works in all supported browsers (Chrome, Firefox, Safari, Edge)
- [ ] Performance is acceptable

### Testing
- Test with small (<1MB) and large (>100MB) files
- Test network failure scenarios
- Test across different browsers

---

## Issue #7: Create static viewer template

**Labels:** `enhancement`, `frontend`, `documentation`, `priority-medium`

### Description
Create a minimal HTML template for deploying static atlas viewers that load data from HF datasets.

### Background
Users should be able to deploy viewers to GitHub Pages, Netlify, HF Spaces, etc. without backend infrastructure.

### Tasks
- [ ] Create `static-viewer-template.html`
- [ ] Include CDN links for embedding-atlas
- [ ] Document metadata.json structure
- [ ] Add example deployment instructions
- [ ] Support customization options (title, theme, initial state)
- [ ] Add browser compatibility checks

### Technical Details
**Files to create:**
- `packages/viewer/static-viewer-template.html`
- `packages/docs/guides/static-viewer-deployment.md`

### Acceptance Criteria
- [ ] Single-file HTML that works standalone
- [ ] Can be deployed to static hosting
- [ ] Clear customization instructions
- [ ] Includes fallback for unsupported browsers
- [ ] Works offline after initial load (with service worker)

### Example Structure
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>My Embedding Atlas</title>
  <script type="module">
    import { coordinator } from '@uwdata/mosaic-core';
    import { EmbeddingAtlas } from 'embedding-atlas';

    // Load configuration from metadata.json
    // Initialize viewer
  </script>
</head>
<body>
  <div id="atlas" style="width: 100vw; height: 100vh;"></div>
</body>
</html>
```

---

## Issue #8: Add remote cache support

**Labels:** `enhancement`, `frontend`, `priority-low`

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
- `packages/viewer/src/app/backend_data_source.ts`
- Cache structure in HF dataset: `cache/*.json`

### Acceptance Criteria
- [ ] Can load pre-computed cache from HF
- [ ] Graceful fallback if cache unavailable
- [ ] Browser storage caching works
- [ ] Cache version mismatches handled properly

---

## Issue #9: Add generate-static-viewer CLI command

**Labels:** `enhancement`, `backend`, `CLI`, `priority-medium`

### Description
Generate a complete static viewer package (HTML + metadata) from an atlas, ready for deployment.

### Dependencies
- Requires Issue #7

### Tasks
- [ ] Add `generate-static-viewer` subcommand to CLI
- [ ] Copy static viewer template
- [ ] Generate metadata.json with correct URLs
- [ ] Optionally include parquet file locally
- [ ] Create deployment README
- [ ] Support both HF dataset and local parquet sources
- [ ] Add options for customization (title, theme, etc.)

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

### Acceptance Criteria
- [ ] Generates complete deployable package
- [ ] Works with both HF and local sources
- [ ] Includes deployment documentation
- [ ] Can customize viewer settings
- [ ] Output is ready for deployment

### Example Usage
```bash
# From HF dataset
embedding-atlas generate-static-viewer \
  --source hf://datasets/username/my-atlas \
  --output ./viewer-dist \
  --title "My Atlas Visualization"

# From local parquet (will upload to HF)
embedding-atlas generate-static-viewer \
  --source my-data.parquet \
  --output ./viewer-dist \
  --upload-to username/my-atlas \
  --title "My Atlas"

# Output structure:
# viewer-dist/
# ├── index.html
# ├── metadata.json
# ├── README.md (deployment instructions)
# └── cache/ (optional)
```

---

## Issue #10: Add HF dataset validation command

**Labels:** `enhancement`, `backend`, `CLI`, `priority-low`

### Description
Validate that an HF dataset has the correct structure and columns for use with Embedding Atlas.

### Dependencies
- Requires Issue #1

### Tasks
- [ ] Add `validate-hf-dataset` subcommand to CLI
- [ ] Check for required columns (projection_x, projection_y)
- [ ] Validate data types
- [ ] Check metadata.json if present
- [ ] Provide helpful fix suggestions
- [ ] Validate __neighbors column format

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

**Files to create:**
- `packages/backend/embedding_atlas/validation.py`

### Acceptance Criteria
- [ ] Identifies missing/incorrect columns
- [ ] Suggests fixes for common issues
- [ ] Works with remote datasets
- [ ] Clear error messages
- [ ] Exit codes indicate success/failure

### Example Usage
```bash
embedding-atlas validate-hf-dataset username/my-atlas

# Output:
# ✓ Dataset accessible
# ✓ Required columns present: projection_x, projection_y, _row_index
# ✓ Data types correct
# ✗ Missing __neighbors column (optional, enables KNN)
# ✓ metadata.json valid
```

---

## Issue #11: Write HF dataset workflow documentation

**Labels:** `documentation`, `priority-high`

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
- `packages/docs/guides/huggingface-datasets.md`
- `packages/docs/guides/static-viewer-deployment.md`
- `packages/docs/guides/troubleshooting-remote-loading.md`

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

---

## Issue #12: Create end-to-end HF workflow example

**Labels:** `documentation`, `example`, `priority-high`

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
- `packages/examples/huggingface_workflow/`
  - `prepare_data.py` - Load and prepare data
  - `export_to_hf.py` - Export to HF
  - `generate_viewer.sh` - Generate static viewer
  - `README.md` - Complete documentation
  - `requirements.txt` - Python dependencies
  - `viewer/` - Generated viewer files
    - `index.html`
    - `metadata.json`

### Acceptance Criteria
- [ ] Complete working example
- [ ] Reproducible steps
- [ ] Deployed demo available
- [ ] Well-documented with explanations
- [ ] Uses realistic dataset

### Example Dataset Suggestions
- Wine reviews (spawn99/wine-reviews)
- ArXiv papers subset
- Movie reviews
- Product descriptions

---

## Issue #13: Add HF dataset examples to docs site

**Labels:** `documentation`, `example`, `priority-medium`

### Description
Add interactive examples using HF datasets to the Embedding Atlas documentation site.

### Dependencies
- Requires Issue #12

### Tasks
- [ ] Add HF dataset examples to docs
- [ ] Embed live static viewers in docs
- [ ] Link to source datasets on HF
- [ ] Add "Try it yourself" sections
- [ ] Create gallery of community atlases

### Technical Details
**Files to modify:**
- `packages/docs/examples.md`
- `packages/docs/gallery.md` (new)

**Files to create:**
- `packages/docs/demos/wine-reviews.html`
- `packages/docs/demos/papers.html`
- `packages/docs/demos/images.html`

### Acceptance Criteria
- [ ] Live demos work on docs site
- [ ] Examples showcase different use cases (text, images, multimodal)
- [ ] Clear instructions for replication
- [ ] Gallery showcases community contributions

---

## Issue #14: Add backend tests for HF integration

**Labels:** `testing`, `backend`, `priority-medium`

### Description
Comprehensive test coverage for HF dataset functionality in the Python backend.

### Dependencies
- Requires Issues #1-#4

### Tasks
- [ ] Test `push_to_hub()` with mocked HF API
- [ ] Test HF URL loading and parsing
- [ ] Test authentication handling
- [ ] Test error cases (network, auth, invalid data)
- [ ] Add integration tests with real HF datasets
- [ ] Test CLI commands

### Technical Details
**Files to create:**
- `packages/backend/tests/test_huggingface.py`
- `packages/backend/tests/test_huggingface_cli.py`

**Testing approach:**
- Unit tests with mocked `huggingface_hub` API
- Integration tests with test HF account
- Fixtures for sample datasets

### Acceptance Criteria
- [ ] >80% code coverage for new features
- [ ] Tests pass in CI
- [ ] Includes both mock and integration tests
- [ ] Tests are fast (<5s for unit tests)
- [ ] Clear test names and documentation

---

## Issue #15: Add frontend tests for remote loading

**Labels:** `testing`, `frontend`, `priority-medium`

### Description
Test suite for remote dataset loading in the viewer.

### Dependencies
- Requires Issues #5-#8

### Tasks
- [ ] Test URL parsing and validation
- [ ] Test DuckDB remote parquet loading
- [ ] Test error handling (network, CORS)
- [ ] Test with mock HTTP responses
- [ ] Add browser compatibility tests
- [ ] Test cache loading

### Technical Details
**Files to create:**
- `packages/viewer/src/__tests__/remote_loading.test.ts`
- `packages/viewer/src/__tests__/mocks/http_server.ts`

### Acceptance Criteria
- [ ] Tests cover core functionality
- [ ] Mock server for testing remote URLs
- [ ] Works in test environment
- [ ] Fast execution (<10s)

---

## Issue #16: Browser compatibility testing

**Labels:** `testing`, `frontend`, `priority-low`

### Description
Comprehensive browser compatibility testing for HF dataset loading.

### Dependencies
- Requires Issues #5-#8

### Tasks
- [ ] Test in Chrome, Firefox, Safari, Edge
- [ ] Test CORS handling
- [ ] Test with various file sizes (1MB, 10MB, 100MB, 1GB)
- [ ] Document browser limitations
- [ ] Add browser detection warnings if needed
- [ ] Test mobile browsers

### Technical Details
**Files to create:**
- `packages/docs/browser-compatibility.md`

### Acceptance Criteria
- [ ] Tested in all major browsers (latest 2 versions)
- [ ] Known issues documented
- [ ] Graceful fallbacks where needed
- [ ] Mobile compatibility verified

### Browser Test Matrix
| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest | ? |
| Firefox | Latest | ? |
| Safari | Latest | ? |
| Edge | Latest | ? |
| Mobile Safari | Latest | ? |
| Mobile Chrome | Latest | ? |

---

## Issue #17: Add progress indicators for remote loading

**Labels:** `enhancement`, `frontend`, `UX`, `priority-medium`

### Description
Show loading progress when fetching remote parquet files to improve user experience.

### Dependencies
- Requires Issue #5

### Background
Large parquet files can take time to load. Users should see:
- Progress indication
- Estimated time remaining
- Current step (fetching, parsing, rendering)

### Tasks
- [ ] Add progress callback to DuckDB loading
- [ ] Show progress bar in UI
- [ ] Estimate time remaining
- [ ] Handle slow connections gracefully
- [ ] Add cancel button for long loads

### Technical Details
**Files to modify:**
- `packages/viewer/src/app/Viewer.svelte`
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/components/LoadingProgress.svelte` (new)

### Acceptance Criteria
- [ ] Progress bar shows during load
- [ ] Accurate progress estimation
- [ ] Works with various file sizes
- [ ] User can cancel load
- [ ] Loading states are clear

---

## Issue #18: Implement chunked loading for large datasets

**Labels:** `enhancement`, `performance`, `priority-low`

### Description
Support loading large datasets in chunks for better performance and memory efficiency.

### Dependencies
- Requires Issue #5

### Background
Very large datasets (>1GB) can cause:
- Long initial load times
- Browser memory issues
- Poor user experience

Chunking allows progressive loading and rendering.

### Tasks
- [ ] Design chunking strategy (spatial, random, etc.)
- [ ] Modify parquet export to create chunks
- [ ] Update frontend to load chunks progressively
- [ ] Render visible chunks first
- [ ] Test with >1GB datasets
- [ ] Document chunking best practices

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/data_source.py`
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/lib/embedding_view/` (progressive rendering)

### Acceptance Criteria
- [ ] Can handle multi-GB datasets
- [ ] Progressive loading works smoothly
- [ ] Performance improvement measurable (quantify)
- [ ] Documentation updated with chunking guide
- [ ] No regression for small datasets

---

## Issue #19: Optimize HTTP range request support

**Labels:** `enhancement`, `performance`, `priority-low`

### Description
Optimize loading by using HTTP range requests instead of full file downloads.

### Dependencies
- Requires Issue #5

### Background
Currently using `forceFullHTTPReads: true` in duckdb.ts:54. HTTP range requests could:
- Speed up initial load by fetching only needed data
- Reduce bandwidth usage
- Enable pagination

### Tasks
- [ ] Research HF support for range requests
- [ ] Implement range request logic in DuckDB config
- [ ] Test with various file sizes
- [ ] Fall back to full downloads if range requests unavailable
- [ ] Measure performance improvement

### Technical Details
**Files to modify:**
- `packages/viewer/src/utils/duckdb.ts` (remove forceFullHTTPReads)

**Current code:**
```typescript
await db.open({
  filesystem: {
    forceFullHTTPReads: true, // <-- Remove this?
  },
});
```

### Acceptance Criteria
- [ ] Uses range requests when HF supports it
- [ ] Fallback to full download works
- [ ] Performance improvement documented
- [ ] No regressions in reliability

---

## Issue #20: Update TypeScript types for HF metadata

**Labels:** `enhancement`, `frontend`, `TypeScript`, `priority-low`

### Description
Update TypeScript interfaces and types to reflect new metadata structure with HF URLs.

### Dependencies
- Requires Issue #5

### Tasks
- [ ] Update `Metadata` interface
- [ ] Add JSDoc comments for new fields
- [ ] Update type exports
- [ ] Generate updated API documentation
- [ ] Add examples to type definitions

### Technical Details
**Files to modify:**
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/api.ts`
- `packages/embedding-atlas/src/index.ts`

### Acceptance Criteria
- [ ] Types are accurate and complete
- [ ] Good IDE autocomplete experience
- [ ] API docs generated and updated
- [ ] Examples in JSDoc

---

## Issue #21: Improve CLI help and documentation

**Labels:** `enhancement`, `CLI`, `documentation`, `priority-low`

### Description
Enhance CLI help text and add comprehensive examples for HF-related commands.

### Dependencies
- Requires Issues #2, #3, #9

### Tasks
- [ ] Add detailed help text for each command
- [ ] Include usage examples in help output
- [ ] Add tips and warnings
- [ ] Create man pages
- [ ] Add shell completion scripts

### Technical Details
**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

### Acceptance Criteria
- [ ] Help text is clear and comprehensive
- [ ] Examples are practical and tested
- [ ] Covers common pitfalls
- [ ] Man pages available
- [ ] Shell completion works (bash, zsh)

---

## Future Enhancement Issues (Phase 8)

### Issue #22: Support incremental dataset updates
**Labels:** `enhancement`, `future`, `priority-low`

Allow updating HF datasets without re-uploading entire parquet file.

### Issue #23: Add dataset versioning support
**Labels:** `enhancement`, `future`, `priority-low`

Support loading specific versions of HF datasets using git refs.

### Issue #24: Add multi-parquet file support
**Labels:** `enhancement`, `future`, `priority-low`

Support atlases split across multiple parquet files with glob patterns.

---

## Issue Templates

For consistency, use these labels:

**Type:**
- `enhancement` - New feature
- `bug` - Bug fix
- `documentation` - Documentation update
- `testing` - Test-related

**Component:**
- `backend` - Python backend
- `frontend` - TypeScript/Svelte frontend
- `CLI` - Command-line interface

**Priority:**
- `priority-high` - Essential for MVP
- `priority-medium` - Important but not blocking
- `priority-low` - Nice to have

**Status:**
- `sprint-1` - MVP features
- `sprint-2` - Complete workflow
- `sprint-3` - Polish & testing
- `sprint-4` - Optimization
- `future` - Future enhancements
