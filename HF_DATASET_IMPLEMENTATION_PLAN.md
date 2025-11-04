# Implementation Plan: Hugging Face Dataset Storage for Embedding Atlas

## Overview

Enable Embedding Atlas to store and load atlas data from Hugging Face datasets, allowing static viewers to load parquet files remotely without requiring a backend server.

## Goals

1. Export atlas data to Hugging Face dataset format
2. Load atlas data from HF dataset URLs in the static viewer
3. Provide CLI commands for HF dataset workflows
4. Create documentation and examples
5. Maintain backward compatibility with existing workflows

---

## Implementation Breakdown

### Phase 1: Core Backend Support (Python)

#### Issue #1: Add Hugging Face dataset export functionality
**Priority:** High | **Complexity:** Medium | **Dependencies:** None

**Description:**
Add capability to export atlas data (parquet + metadata) to Hugging Face datasets.

**Tasks:**
- [ ] Add `push_to_hub()` method to `DataSource` class
- [ ] Export parquet file with all required columns (projection_x, projection_y, __neighbors, etc.)
- [ ] Include metadata.json as a dataset file
- [ ] Handle authentication (HF tokens)
- [ ] Add optional README.md generation with dataset card

**Files to modify:**
- `packages/backend/embedding_atlas/data_source.py`
- `packages/backend/embedding_atlas/cli.py` (add new command)

**Acceptance criteria:**
- Can export complete atlas to HF dataset
- Metadata is preserved
- Dataset is accessible via HF web interface
- Works with both public and private datasets

**Example usage:**
```python
from embedding_atlas import DataSource
ds = DataSource(...)
ds.push_to_hub("username/my-atlas", private=False)
```

---

#### Issue #2: Add CLI command for HF dataset export
**Priority:** High | **Complexity:** Low | **Dependencies:** Issue #1

**Description:**
Add `embedding-atlas export-hf` CLI command to export existing atlas to Hugging Face.

**Tasks:**
- [ ] Add `export-hf` subcommand to CLI
- [ ] Add flags: `--repo-id`, `--private`, `--token`
- [ ] Provide helpful error messages for authentication issues
- [ ] Add progress reporting for upload

**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

**Acceptance criteria:**
- Command successfully exports to HF
- Clear error messages for common issues
- Progress indication during upload
- Help documentation is clear

**Example usage:**
```bash
embedding-atlas export-hf my-data.parquet --repo-id username/my-atlas
```

---

#### Issue #3: Add CLI command to create atlas from HF dataset
**Priority:** Medium | **Complexity:** Medium | **Dependencies:** None

**Description:**
Add `embedding-atlas from-hf` CLI command to load and visualize HF datasets directly.

**Tasks:**
- [ ] Add `from-hf` subcommand to CLI
- [ ] Support `hf://` URLs and repo IDs
- [ ] Auto-detect columns if using standard naming
- [ ] Allow column mapping via flags
- [ ] Download and cache dataset locally

**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`
- `packages/backend/embedding_atlas/utils.py`

**Acceptance criteria:**
- Can load atlas from HF dataset URL
- Works with various HF dataset formats
- Respects local caching
- Clear error messages for missing columns

**Example usage:**
```bash
embedding-atlas from-hf username/my-atlas
embedding-atlas from-hf hf://datasets/username/my-atlas
```

---

#### Issue #4: Update `determine_and_load_data()` to support HF URLs
**Priority:** Medium | **Complexity:** Low | **Dependencies:** None

**Description:**
Extend data loading to accept `hf://` URLs and HF repo IDs as data sources.

**Tasks:**
- [ ] Detect HF URLs in data path
- [ ] Use `datasets.load_dataset()` for HF sources
- [ ] Handle authentication for private datasets
- [ ] Add caching behavior

**Files to modify:**
- `packages/backend/embedding_atlas/utils.py`

**Acceptance criteria:**
- Can pass HF URLs to existing commands
- Works seamlessly with current API
- Backward compatible

**Example usage:**
```bash
embedding-atlas hf://datasets/username/my-atlas
```

---

### Phase 2: Frontend Support (TypeScript)

#### Issue #5: Support remote dataset URLs in metadata
**Priority:** High | **Complexity:** Medium | **Dependencies:** None

**Description:**
Update `BackendDataSource` to support loading parquet from arbitrary HTTP(S) and `hf://` URLs.

**Tasks:**
- [ ] Extend `Metadata` interface to support `datasetUrl` field
- [ ] Modify initialization to use custom URL if provided
- [ ] Handle both absolute and relative URLs
- [ ] Add error handling for CORS issues
- [ ] Test with HF dataset URLs

**Files to modify:**
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/app/data_source.ts` (interface)

**Acceptance criteria:**
- Can load parquet from HF URLs
- Works with `hf://` protocol
- Clear error messages for network issues
- Maintains compatibility with local URLs

**Example metadata.json:**
```json
{
  "database": {
    "type": "wasm",
    "load": true,
    "datasetUrl": "hf://datasets/username/atlas@~parquet/**/*.parquet"
  }
}
```

---

#### Issue #6: Add DuckDB httpfs extension support
**Priority:** High | **Complexity:** Medium | **Dependencies:** Issue #5

**Description:**
Ensure DuckDB WASM has httpfs extension installed and configured for remote file access.

**Tasks:**
- [ ] Check if httpfs is included in current DuckDB WASM build
- [ ] Add httpfs installation/loading if needed
- [ ] Configure HTTP settings for browser compatibility
- [ ] Test with various remote parquet sources
- [ ] Add retry logic for network failures

**Files to modify:**
- `packages/viewer/src/utils/duckdb.ts`
- `packages/viewer/src/utils/database.ts`

**Acceptance criteria:**
- Can read remote parquet via HTTP(S)
- `hf://` URLs work correctly
- Handles network errors gracefully
- Works in all supported browsers

---

#### Issue #7: Create static viewer template
**Priority:** Medium | **Complexity:** Low | **Dependencies:** Issue #5

**Description:**
Create a minimal HTML template for deploying static atlas viewers.

**Tasks:**
- [ ] Create `static-viewer-template.html`
- [ ] Include CDN links for embedding-atlas
- [ ] Document metadata.json structure
- [ ] Add example deployment instructions
- [ ] Support customization options (title, theme, etc.)

**Files to create:**
- `packages/viewer/static-viewer-template.html`
- `packages/docs/static-viewer-guide.md`

**Acceptance criteria:**
- Single-file HTML that works standalone
- Can be deployed to GitHub Pages, Netlify, etc.
- Clear customization instructions
- Includes fallback for unsupported browsers

**Example structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>My Atlas</title>
  <script src="https://cdn.jsdelivr.net/npm/embedding-atlas@latest"></script>
</head>
<body>
  <div id="atlas"></div>
  <script type="module">
    // Load from metadata.json
  </script>
</body>
</html>
```

---

#### Issue #8: Add cache remote URL support
**Priority:** Low | **Complexity:** Low | **Dependencies:** Issue #5

**Description:**
Support loading cached data (labels, etc.) from remote URLs alongside dataset.

**Tasks:**
- [ ] Extend cache interface to support remote URLs
- [ ] Load cache files from HF dataset if available
- [ ] Fall back to generating cache if not found
- [ ] Store generated cache in browser storage

**Files to modify:**
- `packages/viewer/src/app/backend_data_source.ts`

**Acceptance criteria:**
- Can load pre-computed cache from HF
- Graceful fallback if cache unavailable
- Browser storage caching works

---

### Phase 3: CLI Enhancements

#### Issue #9: Add `generate-static-viewer` CLI command
**Priority:** Medium | **Complexity:** Medium | **Dependencies:** Issue #7

**Description:**
Generate a complete static viewer package (HTML + metadata) from an atlas.

**Tasks:**
- [ ] Add `generate-static-viewer` subcommand
- [ ] Copy static viewer template
- [ ] Generate metadata.json with correct URLs
- [ ] Optionally bundle parquet file locally
- [ ] Create README with deployment instructions
- [ ] Support HF dataset or local parquet sources

**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

**Acceptance criteria:**
- Generates complete deployable package
- Works with both HF and local sources
- Includes deployment documentation
- Can customize viewer settings

**Example usage:**
```bash
# From HF dataset
embedding-atlas generate-static-viewer \
  --source hf://datasets/username/my-atlas \
  --output ./viewer-dist

# From local parquet
embedding-atlas generate-static-viewer \
  --source my-data.parquet \
  --output ./viewer-dist \
  --upload-to username/my-atlas
```

---

#### Issue #10: Add validation command for HF datasets
**Priority:** Low | **Complexity:** Low | **Dependencies:** Issue #1

**Description:**
Validate that an HF dataset has the correct structure for Embedding Atlas.

**Tasks:**
- [ ] Add `validate-hf-dataset` subcommand
- [ ] Check for required columns
- [ ] Validate data types
- [ ] Check metadata.json if present
- [ ] Provide helpful fix suggestions

**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`
- `packages/backend/embedding_atlas/validation.py` (new file)

**Acceptance criteria:**
- Identifies missing/incorrect columns
- Suggests fixes for common issues
- Works with remote datasets
- Clear error messages

**Example usage:**
```bash
embedding-atlas validate-hf-dataset username/my-atlas
```

---

### Phase 4: Documentation & Examples

#### Issue #11: Write HF dataset workflow documentation
**Priority:** High | **Complexity:** Low | **Dependencies:** Issues #1-#10

**Description:**
Comprehensive guide for the HF dataset workflow.

**Tasks:**
- [ ] Create "Working with Hugging Face Datasets" guide
- [ ] Document export workflow
- [ ] Document static viewer deployment
- [ ] Add troubleshooting section
- [ ] Include architecture diagrams
- [ ] Add best practices (file size, chunking, etc.)

**Files to create:**
- `packages/docs/huggingface-datasets.md`

**Acceptance criteria:**
- Complete end-to-end workflow documented
- Covers common use cases
- Includes troubleshooting
- Has working examples

**Topics to cover:**
- Exporting atlas to HF
- Loading from HF in Python
- Creating static viewers
- Deployment options
- Performance considerations
- Private vs public datasets

---

#### Issue #12: Create end-to-end example
**Priority:** High | **Complexity:** Medium | **Dependencies:** Issues #1-#10

**Description:**
Create a complete working example demonstrating the HF dataset workflow.

**Tasks:**
- [ ] Create example Python script
- [ ] Use a public dataset (e.g., wine reviews)
- [ ] Generate embeddings and projections
- [ ] Export to HF dataset
- [ ] Create static viewer
- [ ] Deploy to GitHub Pages or HF Spaces
- [ ] Document all steps

**Files to create:**
- `packages/examples/huggingface_workflow/`
  - `prepare_data.py`
  - `export_to_hf.py`
  - `generate_viewer.sh`
  - `README.md`
  - `viewer/index.html`
  - `viewer/metadata.json`

**Acceptance criteria:**
- Complete working example
- Reproducible steps
- Deployed demo available
- Well-documented

---

#### Issue #13: Add HF dataset examples to docs site
**Priority:** Medium | **Complexity:** Low | **Dependencies:** Issue #12

**Description:**
Add interactive examples using HF datasets to the documentation site.

**Tasks:**
- [ ] Add HF dataset examples to docs
- [ ] Embed live static viewers
- [ ] Link to source datasets on HF
- [ ] Add "Try it yourself" sections

**Files to modify:**
- `packages/docs/examples.md`
- `packages/docs/demos/hf-*.html` (new files)

**Acceptance criteria:**
- Live demos work on docs site
- Examples showcase different use cases
- Clear instructions for replication

---

### Phase 5: Testing & Quality Assurance

#### Issue #14: Add backend tests for HF integration
**Priority:** Medium | **Complexity:** Medium | **Dependencies:** Issues #1-#4

**Description:**
Comprehensive test coverage for HF dataset functionality.

**Tasks:**
- [ ] Test `push_to_hub()` (with mock)
- [ ] Test HF URL loading
- [ ] Test authentication handling
- [ ] Test error cases
- [ ] Add integration tests with real HF datasets

**Files to create/modify:**
- `packages/backend/tests/test_huggingface.py`

**Acceptance criteria:**
- >80% code coverage for new features
- Tests pass in CI
- Includes mock and integration tests

---

#### Issue #15: Add frontend tests for remote loading
**Priority:** Medium | **Complexity:** Medium | **Dependencies:** Issues #5-#8

**Description:**
Test remote dataset loading in the frontend.

**Tasks:**
- [ ] Test URL parsing and validation
- [ ] Test DuckDB remote parquet loading
- [ ] Test error handling
- [ ] Test with mock HTTP responses
- [ ] Add browser compatibility tests

**Files to create/modify:**
- `packages/viewer/src/__tests__/remote_loading.test.ts`

**Acceptance criteria:**
- Tests cover core functionality
- Mock server for testing
- Works in test environment

---

#### Issue #16: Browser compatibility testing
**Priority:** Low | **Complexity:** Medium | **Dependencies:** Issues #5-#8

**Description:**
Ensure HF dataset loading works across browsers.

**Tasks:**
- [ ] Test in Chrome, Firefox, Safari, Edge
- [ ] Test CORS handling
- [ ] Test with various file sizes
- [ ] Document browser limitations
- [ ] Add browser detection warnings if needed

**Files to create/modify:**
- `packages/docs/browser-compatibility.md`

**Acceptance criteria:**
- Works in all major browsers
- Known issues documented
- Graceful fallbacks where needed

---

### Phase 6: Performance & Optimization

#### Issue #17: Add progress indicators for remote loading
**Priority:** Medium | **Complexity:** Low | **Dependencies:** Issue #5

**Description:**
Show loading progress when fetching remote parquet files.

**Tasks:**
- [ ] Add progress callback to DuckDB loading
- [ ] Show progress bar in UI
- [ ] Estimate time remaining
- [ ] Handle slow connections gracefully

**Files to modify:**
- `packages/viewer/src/app/Viewer.svelte`
- `packages/viewer/src/app/backend_data_source.ts`

**Acceptance criteria:**
- Progress bar shows during load
- Accurate progress estimation
- Works with various file sizes

---

#### Issue #18: Implement chunked loading for large datasets
**Priority:** Low | **Complexity:** High | **Dependencies:** Issue #5

**Description:**
Support loading large datasets in chunks for better performance.

**Tasks:**
- [ ] Design chunking strategy
- [ ] Modify parquet export to create chunks
- [ ] Update frontend to load chunks progressively
- [ ] Test with >1GB datasets
- [ ] Document chunking best practices

**Files to modify:**
- `packages/backend/embedding_atlas/data_source.py`
- `packages/viewer/src/app/backend_data_source.ts`

**Acceptance criteria:**
- Can handle multi-GB datasets
- Progressive loading works
- Performance improvement measurable
- Documentation updated

---

#### Issue #19: Add HTTP range request support
**Priority:** Low | **Complexity:** Medium | **Dependencies:** Issue #5

**Description:**
Optimize loading by using HTTP range requests (if supported by HF).

**Tasks:**
- [ ] Research HF support for range requests
- [ ] Implement range request logic
- [ ] Test with various file sizes
- [ ] Fall back to full downloads if unavailable

**Files to modify:**
- `packages/viewer/src/utils/duckdb.ts`

**Acceptance criteria:**
- Uses range requests when available
- Fallback to full download works
- Performance improvement documented

**Note:** Currently disabled via `forceFullHTTPReads: true` in duckdb.ts:54

---

### Phase 7: Developer Experience

#### Issue #20: Add TypeScript types for metadata with HF URLs
**Priority:** Low | **Complexity:** Low | **Dependencies:** Issue #5

**Description:**
Update TypeScript interfaces to reflect new metadata structure.

**Tasks:**
- [ ] Update `Metadata` interface
- [ ] Add JSDoc comments
- [ ] Update type exports
- [ ] Generate updated API documentation

**Files to modify:**
- `packages/viewer/src/app/backend_data_source.ts`
- `packages/viewer/src/api.ts`

**Acceptance criteria:**
- Types are accurate
- Good IDE autocomplete
- API docs updated

---

#### Issue #21: Add CLI help and examples
**Priority:** Low | **Complexity:** Low | **Dependencies:** Issues #2, #3, #9

**Description:**
Improve CLI help documentation for HF commands.

**Tasks:**
- [ ] Add detailed help text for each command
- [ ] Include usage examples
- [ ] Add tips and warnings
- [ ] Create man pages

**Files to modify:**
- `packages/backend/embedding_atlas/cli.py`

**Acceptance criteria:**
- Help text is clear and comprehensive
- Examples are practical
- Covers common pitfalls

---

### Phase 8: Advanced Features (Future)

#### Issue #22: Support incremental dataset updates
**Priority:** Low | **Complexity:** High | **Dependencies:** Issue #1

**Description:**
Allow updating HF datasets without re-uploading entire parquet file.

**Tasks:**
- [ ] Design delta update strategy
- [ ] Implement append-only updates
- [ ] Handle metadata updates
- [ ] Version control strategy

**Acceptance criteria:**
- Can update without full re-upload
- Maintains data integrity
- Works with HF versioning

---

#### Issue #23: Add dataset versioning support
**Priority:** Low | **Complexity:** Medium | **Dependencies:** Issue #1

**Description:**
Support loading specific versions of HF datasets.

**Tasks:**
- [ ] Support git refs in URLs
- [ ] Add version selector in viewer
- [ ] Document versioning workflow

**Acceptance criteria:**
- Can load specific dataset versions
- Version selector works in UI
- Compatible with HF versioning

---

#### Issue #24: Add multi-parquet file support
**Priority:** Low | **Complexity:** Medium | **Dependencies:** Issue #5

**Description:**
Support atlases split across multiple parquet files.

**Tasks:**
- [ ] Support glob patterns in dataset URLs
- [ ] Merge multiple parquet files in DuckDB
- [ ] Handle sharding strategies
- [ ] Document when to use multiple files

**Acceptance criteria:**
- Can load from multiple parquet files
- Performance is acceptable
- Documentation clear

---

## Suggested Implementation Order

### Sprint 1: MVP (Core Functionality)
1. Issue #1: Export to HF
2. Issue #2: CLI export command
3. Issue #5: Remote URL support in frontend
4. Issue #6: DuckDB httpfs extension
5. Issue #11: Basic documentation

### Sprint 2: Complete Workflow
6. Issue #3: CLI from-hf command
7. Issue #7: Static viewer template
8. Issue #9: Generate static viewer CLI
9. Issue #12: End-to-end example
10. Issue #4: Update data loading

### Sprint 3: Polish & Testing
11. Issue #14: Backend tests
12. Issue #15: Frontend tests
13. Issue #17: Progress indicators
14. Issue #13: Docs site examples
15. Issue #10: Validation command

### Sprint 4: Optimization & Extras
16. Issue #8: Remote cache support
17. Issue #16: Browser compatibility
18. Issue #20: TypeScript types
19. Issue #21: CLI help improvements

### Future Sprints
20. Issue #18: Chunked loading
21. Issue #19: HTTP range requests
22. Issue #22: Incremental updates
23. Issue #23: Dataset versioning
24. Issue #24: Multi-parquet support

---

## Success Metrics

1. **Adoption**: Number of atlases published to HF
2. **Performance**: Load time for typical datasets (<10s for 100k points)
3. **Reliability**: Success rate of remote loading (>95%)
4. **Documentation**: User satisfaction with guides
5. **Developer Experience**: Time from atlas creation to deployed viewer (<5 minutes)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| HF rate limiting | Add retry logic, document limits |
| Large file sizes | Implement chunking, compression |
| CORS issues | Clear documentation, error messages |
| Browser compatibility | Test across browsers, provide fallbacks |
| Breaking changes | Maintain backward compatibility, version APIs |

---

## Open Questions

1. Should we support other remote storage (S3, GCS, Azure)?
2. How to handle authentication for private datasets in static viewers?
3. Should we create HF Space templates?
4. What's the strategy for very large datasets (>5GB)?
5. Should we bundle a subset of data for initial render?

---

## Resources Needed

- Access to HF datasets API documentation
- Test HF account for integration testing
- Browser testing infrastructure
- Performance benchmarking tools
- Example datasets of various sizes

---

## Timeline Estimate

- **MVP (Sprint 1)**: 2 weeks
- **Complete Workflow (Sprint 2)**: 2 weeks
- **Polish & Testing (Sprint 3)**: 1-2 weeks
- **Optimization (Sprint 4)**: 1 week
- **Total**: 6-7 weeks for full implementation

---

## Related Work

- DuckDB HF integration: https://duckdb.org/docs/stable/core_extensions/httpfs/hugging_face
- HF Parquet documentation: https://huggingface.co/docs/dataset-viewer/en/parquet
- Observable HF examples: https://observablehq.com/@huggingface/explore-hugging-face-datasets-with-parquet
