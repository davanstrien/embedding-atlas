# Copyright (c) 2025 Apple Inc. Licensed under MIT License.

import json
import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd

from .utils import cache_path, to_parquet_bytes


class DataSource:
    def __init__(
        self,
        identifier: str,
        dataset: pd.DataFrame,
        metadata: dict,
    ):
        self.identifier = identifier
        self.dataset = dataset
        self.metadata = metadata
        self.cache_path = cache_path("cache", self.identifier)

    def cache_set(self, name: str, data):
        path = self.cache_path / name
        with open(path, "w") as f:
            json.dump(data, f)

    def cache_get(self, name: str):
        path = self.cache_path / name
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        else:
            return None

    def make_archive(self, static_path: str):
        io = BytesIO()
        with zipfile.ZipFile(io, "w", zipfile.ZIP_DEFLATED) as zip:
            zip.writestr(
                "data/metadata.json",
                json.dumps(
                    self.metadata
                    | {"isStatic": True, "database": {"type": "wasm", "load": True}}
                ),
            )
            zip.writestr("data/dataset.parquet", to_parquet_bytes(self.dataset))
            for root, _, files in os.walk(static_path):
                for fn in files:
                    p = os.path.relpath(os.path.join(root, fn), static_path)
                    zip.write(os.path.join(root, fn), p)
            for root, _, files in os.walk(self.cache_path):
                for fn in files:
                    p = os.path.join(
                        "data/cache",
                        os.path.relpath(os.path.join(root, fn), str(self.cache_path)),
                    )
                    zip.write(os.path.join(root, fn), p)
        return io.getvalue()

    def push_to_hub(
        self,
        repo_id: str,
        *,
        private: bool = False,
        token: Optional[str] = None,
        commit_message: Optional[str] = None,
        create_pr: bool = False,
    ) -> str:
        """
        Push the atlas dataset to Hugging Face Hub.

        Args:
            repo_id: The repository ID on Hugging Face Hub (e.g., "username/dataset-name")
            private: Whether to create a private dataset (default: False)
            token: Hugging Face API token. If not provided, will use HF_TOKEN env variable
            commit_message: Custom commit message (default: "Upload embedding atlas dataset")
            create_pr: Create a pull request instead of committing directly (default: False)

        Returns:
            The URL of the uploaded dataset

        Example:
            >>> ds = DataSource(identifier="my-atlas", dataset=df, metadata=metadata)
            >>> url = ds.push_to_hub("username/my-atlas", private=False)
            >>> print(f"Dataset uploaded to: {url}")
        """
        try:
            from huggingface_hub import HfApi, create_repo
        except ImportError:
            raise ImportError(
                "huggingface_hub is required to push to Hugging Face. "
                "Install it with: pip install huggingface-hub"
            )

        # Use default commit message if not provided
        if commit_message is None:
            commit_message = "Upload embedding atlas dataset"

        # Initialize HF API
        api = HfApi(token=token)

        # Create repository if it doesn't exist
        try:
            repo_url = create_repo(
                repo_id=repo_id,
                repo_type="dataset",
                private=private,
                exist_ok=True,
                token=token,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create repository: {e}")

        # Use a temporary directory to prepare files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save the parquet file
            parquet_path = temp_path / "dataset.parquet"
            self.dataset.to_parquet(parquet_path, index=False)

            # Save metadata with HF-specific configuration
            metadata_path = temp_path / "metadata.json"
            hf_metadata = self.metadata.copy()
            hf_metadata["database"] = {
                "type": "wasm",
                "load": True,
                "datasetUrl": f"hf://datasets/{repo_id}@~parquet/**/*.parquet",
            }
            with open(metadata_path, "w") as f:
                json.dump(hf_metadata, f, indent=2)

            # Save cache files if they exist
            if self.cache_path.exists():
                cache_dir = temp_path / "cache"
                cache_dir.mkdir(exist_ok=True)
                for cache_file in self.cache_path.glob("*.json"):
                    target = cache_dir / cache_file.name
                    target.write_text(cache_file.read_text())

            # Generate README with dataset card
            readme_path = temp_path / "README.md"
            readme_content = self._generate_readme(repo_id)
            with open(readme_path, "w") as f:
                f.write(readme_content)

            # Upload all files
            try:
                api.upload_folder(
                    folder_path=str(temp_path),
                    repo_id=repo_id,
                    repo_type="dataset",
                    commit_message=commit_message,
                    create_pr=create_pr,
                    token=token,
                )
            except Exception as e:
                raise RuntimeError(f"Failed to upload files to Hugging Face: {e}")

        return f"https://huggingface.co/datasets/{repo_id}"

    def _generate_readme(self, repo_id: str) -> str:
        """Generate a README.md for the HF dataset."""
        num_rows = len(self.dataset)
        columns = list(self.dataset.columns)

        # Get text column if specified
        text_col = self.metadata.get("props", {}).get("data", {}).get("text")

        readme = f"""---
license: mit
tags:
  - embedding-atlas
  - embeddings
  - visualization
size_categories:
  - n<1K
  - 1K<n<10K
  - 10K<n<100K
  - 100K<n<1M
  - 1M<n<10M
---

# Embedding Atlas Dataset

This dataset contains embedding projections and metadata for use with [Embedding Atlas](https://apple.github.io/embedding-atlas).

## Dataset Information

- **Repository:** {repo_id}
- **Number of rows:** {num_rows:,}
- **Columns:** {len(columns)}

## Columns

{self._format_columns(columns)}

## Usage

### With Embedding Atlas CLI

```bash
# Install embedding-atlas
pip install embedding-atlas

# View the dataset
embedding-atlas from-hf {repo_id}
```

### With Python

```python
from embedding_atlas import load_dataset

# Load the dataset
df = load_dataset("hf://datasets/{repo_id}")

# Or use with Hugging Face datasets
from datasets import load_dataset
ds = load_dataset("{repo_id}")
```

### Static Viewer

You can create a static viewer that loads this dataset:

```bash
embedding-atlas generate-static-viewer \\
  --source hf://datasets/{repo_id} \\
  --output ./viewer
```

## Viewing the Data

This dataset can be visualized directly at:
- [Embedding Atlas Viewer](https://apple.github.io/embedding-atlas) (upload the parquet file)
- Or deploy your own static viewer using the instructions above

## Dataset Structure

The dataset includes:
- `dataset.parquet`: Main data file with embeddings and projections
- `metadata.json`: Configuration for the Embedding Atlas viewer
- `cache/`: Pre-computed labels and clusters (if available)

## Citation

If you use this dataset, please cite Embedding Atlas:

```bibtex
@misc{{ren2025embedding,
  title={{Embedding Atlas: Low-Friction, Interactive Embedding Visualization}},
  author={{Donghao Ren and Fred Hohman and Halden Lin and Dominik Moritz}},
  year={{2025}},
  eprint={{2505.06386}},
  archivePrefix={{arXiv}},
  primaryClass={{cs.HC}},
  url={{https://arxiv.org/abs/2505.06386}},
}}
```

## License

MIT License
"""
        return readme

    def _format_columns(self, columns: list) -> str:
        """Format column list for README."""
        essential_cols = ["projection_x", "projection_y", "_row_index", "__neighbors"]
        formatted = []

        for col in columns:
            if col in essential_cols:
                if col == "projection_x":
                    formatted.append(f"- `{col}`: X coordinate of 2D projection")
                elif col == "projection_y":
                    formatted.append(f"- `{col}`: Y coordinate of 2D projection")
                elif col == "_row_index":
                    formatted.append(f"- `{col}`: Unique row identifier")
                elif col == "__neighbors":
                    formatted.append(f"- `{col}`: Pre-computed K-nearest neighbors")
            else:
                formatted.append(f"- `{col}`: Data column")

        return "\n".join(formatted)
