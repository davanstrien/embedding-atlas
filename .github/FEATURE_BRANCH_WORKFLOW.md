# HF Dataset Integration - Development Workflow

This document describes the development workflow for the Hugging Face dataset integration feature.

## Branch Structure

```
main (upstream)
  └── claude/feature-hf-dataset-support-011CUoMb7WaT4m5BDDgzSkxf (feature branch)
        ├── claude/issue-1-hf-export-011CUoMb7WaT4m5BDDgzSkxf (PR against feature branch)
        ├── claude/issue-2-cli-export-011CUoMb7WaT4m5BDDgzSkxf (PR against feature branch)
        ├── claude/issue-4-data-loading-011CUoMb7WaT4m5BDDgzSkxf (PR against feature branch)
        ├── claude/issue-5-remote-urls-011CUoMb7WaT4m5BDDgzSkxf (PR against feature branch)
        └── claude/issue-6-duckdb-httpfs-011CUoMb7WaT4m5BDDgzSkxf (PR against feature branch)
```

## Getting Started

### 1. Create GitHub Issues

Run the issue creation script on your local machine:

```bash
./create_github_issues.sh
```

This will create all 21+ issues in your GitHub repository with proper labels and organization.

### 2. Review Planning Documents

- **HF_DATASET_IMPLEMENTATION_PLAN.md** - Complete technical plan
- **HF_DATASET_GITHUB_ISSUES.md** - Detailed issue templates
- **HF_DATASET_QUICK_START.md** - Quick reference

### 3. Development Workflow

Each issue is implemented in a separate branch that PRs against the feature branch:

1. Branch from feature branch: `claude/feature-hf-dataset-support-011CUoMb7WaT4m5BDDgzSkxf`
2. Implement the feature with tests
3. Open PR against the feature branch (not main)
4. Review and merge into feature branch
5. When all features are complete, open final PR from feature branch to main

## Sprint Organization

### Sprint 1: MVP (2 weeks)
Core functionality to export and load HF datasets:

- [ ] Issue #1: HF export functionality (backend)
- [ ] Issue #2: CLI export command
- [ ] Issue #5: Remote URL support (frontend)
- [ ] Issue #6: DuckDB httpfs extension
- [ ] Issue #11: Basic documentation

### Sprint 2: Complete Workflow (2 weeks)
Full CLI workflow and static viewer:

- [ ] Issue #3: CLI from-hf command
- [ ] Issue #4: Update data loading
- [ ] Issue #7: Static viewer template
- [ ] Issue #9: Generate static viewer CLI
- [ ] Issue #12: End-to-end example

### Sprint 3: Polish (1-2 weeks)
Testing and UX improvements:

- [ ] Issue #10: Validation command
- [ ] Issue #13: Docs examples
- [ ] Issue #14: Backend tests
- [ ] Issue #15: Frontend tests
- [ ] Issue #17: Progress indicators

### Sprint 4: Optimization (1 week)
Performance and developer experience:

- [ ] Issue #8: Remote cache support
- [ ] Issue #16: Browser compatibility
- [ ] Issue #20: TypeScript types
- [ ] Issue #21: CLI help

## Implementation Status

### Completed
- [x] Planning and documentation
- [x] Feature branch setup
- [x] Issue creation script

### In Progress
- [ ] Issue #1: HF export functionality
- [ ] Issue #2: CLI export command
- [ ] Issue #4: Data loading updates
- [ ] Issue #5: Remote URL support
- [ ] Issue #6: DuckDB httpfs

### Pending
- [ ] All other issues

## Creating Pull Requests

Since PRs are created against the feature branch, use:

```bash
# For each issue branch
gh pr create \
  --base claude/feature-hf-dataset-support-011CUoMb7WaT4m5BDDgzSkxf \
  --head claude/issue-X-...-011CUoMb7WaT4m5BDDgzSkxf \
  --title "feat: [Issue #X] Title" \
  --body "Closes #X"
```

Or visit the PR creation URL provided when pushing branches.

## Testing

Each PR should include:
- [ ] Unit tests for new functionality
- [ ] Integration tests where applicable
- [ ] Manual testing verification
- [ ] Documentation updates
- [ ] No breaking changes to existing API

## Merging Strategy

1. **Issue PRs → Feature Branch**: Individual features are merged into the feature branch after review
2. **Feature Branch → Main**: Once all Sprint 1-2 issues are complete and tested, create a final PR to main

## Non-Breaking Change Principles

All implementations must:
- ✅ Add new functionality without modifying existing behavior
- ✅ Use optional parameters with sensible defaults
- ✅ Maintain backward compatibility
- ✅ Add comprehensive tests
- ✅ Include documentation

## Questions?

Refer to:
- Planning docs in this repository
- GitHub issues for specific feature details
- Implementation plan for technical architecture
