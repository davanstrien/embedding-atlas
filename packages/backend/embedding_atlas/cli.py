# Copyright (c) 2025 Apple Inc. Licensed under MIT License.

"""Command line interface."""

import logging
import pathlib
import socket
from pathlib import Path

import click
import inquirer
import numpy as np
import pandas as pd
import uvicorn

from .data_source import DataSource
from .options import make_embedding_atlas_props
from .server import make_server
from .utils import Hasher, load_huggingface_data, load_pandas_data
from .version import __version__


def find_column_name(existing_names, candidate):
    if candidate not in existing_names:
        return candidate
    else:
        index = 1
        while True:
            s = f"{candidate}_{index}"
            if s not in existing_names:
                return s
            index += 1


def determine_and_load_data(filename: str, splits: list[str] | None = None):
    suffix = Path(filename).suffix.lower()
    hf_prefix = "hf://datasets/"

    # Override Hugging Face data if given full url
    if filename.startswith(hf_prefix):
        filename = filename.split(hf_prefix)[-1]

    # Hugging Face data
    if (len(filename.split("/")) <= 2) and (suffix == ""):
        df = load_huggingface_data(filename, splits)
    else:
        df = load_pandas_data(filename)

    return df


def load_datasets(
    inputs: list[str], splits: list[str] | None = None, sample: int | None = None
) -> pd.DataFrame:
    existing_column_names = set()
    dataframes = []
    for fn in inputs:
        print("Loading data from " + fn)
        df = determine_and_load_data(fn, splits=splits)
        dataframes.append(df)
        for c in df.columns:
            existing_column_names.add(c)

    file_name_column = find_column_name(existing_column_names, "FILE_NAME")
    for df, fn in zip(dataframes, inputs):
        df[file_name_column] = fn

    df = pd.concat(dataframes)

    if sample:
        df = df.sample(n=sample, axis=0, random_state=np.random.RandomState(42))

    return df


def prompt_for_column(df: pd.DataFrame, message: str) -> str | None:
    question = [
        inquirer.List(
            "arg",
            message=message,
            choices=sorted(["(none)"] + [str(c) for c in df.columns]),
        ),
    ]
    r = inquirer.prompt(question)
    if r is None:
        return None
    text = r["arg"]  # type: ignore
    if text == "(none)":
        text = None
    return text


def find_available_port(start_port: int, max_attempts: int = 10, host="localhost"):
    """Find the next available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("No available ports found in the given range")


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__, package_name="embedding_atlas")
def cli(ctx):
    """Embedding Atlas - Interactive visualization for large embeddings.

    Run without subcommands to start the viewer (legacy behavior).
    Use subcommands for additional functionality:

      export-hf  Export atlas to Hugging Face dataset
    """
    # If no subcommand is given, invoke the default serve command
    if ctx.invoked_subcommand is None:
        ctx.invoke(serve)


@cli.command(name="serve", hidden=True)
@click.argument("inputs", nargs=-1, required=True)
@click.option("--text", default=None, help="Column containing text data.")
@click.option("--image", default=None, help="Column containing image data.")
@click.option(
    "--vector", default=None, help="Column containing pre-computed vector embeddings."
)
@click.option(
    "--split",
    default=[],
    multiple=True,
    help="Dataset split name(s) to load from Hugging Face datasets. Can be specified multiple times for multiple splits.",
)
@click.option(
    "--enable-projection/--disable-projection",
    "enable_projection",
    default=True,
    help="Compute embedding projections from text/image/vector data. If disabled without pre-computed projections, the embedding view will be unavailable.",
)
@click.option(
    "--model",
    default=None,
    help="Model name for generating embeddings (e.g., 'all-MiniLM-L6-v2').",
)
@click.option(
    "--trust-remote-code",
    is_flag=True,
    default=False,
    help="Allow execution of remote code when loading models from Hugging Face Hub.",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Batch size for processing embeddings (default: 32 for text, 16 for images). Larger values use more memory but may be faster.",
)
@click.option(
    "--x",
    "x_column",
    help="Column containing pre-computed X coordinates for the embedding view.",
)
@click.option(
    "--y",
    "y_column",
    help="Column containing pre-computed Y coordinates for the embedding view.",
)
@click.option(
    "--neighbors",
    "neighbors_column",
    help='Column containing pre-computed nearest neighbors in format: {"ids": [n1, n2, ...], "distances": [d1, d2, ...]}. IDs should be zero-based row indices.',
)
@click.option(
    "--sample",
    default=None,
    type=int,
    help="Number of random samples to draw from the dataset. Useful for large datasets.",
)
@click.option(
    "--umap-n-neighbors",
    type=int,
    help="Number of neighbors to consider for UMAP dimensionality reduction (default: 15).",
)
@click.option(
    "--umap-min-dist",
    type=float,
    help="The min_dist parameter for UMAP.",
)
@click.option(
    "--umap-metric",
    default="cosine",
    help="Distance metric for UMAP computation (default: 'cosine').",
)
@click.option(
    "--umap-random-state", type=int, help="Random seed for reproducible UMAP results."
)
@click.option(
    "--duckdb",
    type=str,
    default="server",
    help="DuckDB connection mode: 'wasm' (run in browser), 'server' (run on this server), or URI (e.g., 'ws://localhost:3000').",
)
@click.option(
    "--host",
    default="localhost",
    help="Host address for the web server (default: localhost).",
)
@click.option(
    "--port", default=5055, help="Port number for the web server (default: 5055)."
)
@click.option(
    "--auto-port/--no-auto-port",
    "enable_auto_port",
    default=True,
    help="Automatically find an available port if the specified port is in use.",
)
@click.option(
    "--static", type=str, help="Custom path to frontend static files directory."
)
@click.option(
    "--export-application",
    type=str,
    help="Export the visualization as a standalone web application to the specified ZIP file and exit.",
)
@click.option(
    "--point-size",
    type=float,
    default=None,
    help="Size of points in the embedding view (default: automatically calculated based on density).",
)
@click.option(
    "--stop-words",
    type=str,
    default=None,
    help="Path to a file containing stop words to exclude from the text embedding. The file should be a data frame with column 'word'",
)
@click.option(
    "--labels",
    type=str,
    default=None,
    help="Path to a file containing labels for the embedding view. The file should be a data frame with columns 'x', 'y', 'text', and optionally 'level' and 'priority'",
)
def serve(
    inputs,
    text: str | None,
    image: str | None,
    vector: str | None,
    split: list[str] | None,
    enable_projection: bool,
    model: str | None,
    trust_remote_code: bool,
    batch_size: int | None,
    x_column: str | None,
    y_column: str | None,
    neighbors_column: str | None,
    sample: int | None,
    umap_n_neighbors: int | None,
    umap_min_dist: int | None,
    umap_metric: str | None,
    umap_random_state: int | None,
    static: str | None,
    duckdb: str,
    host: str,
    port: int,
    enable_auto_port: bool,
    export_application: str | None,
    point_size: float | None,
    stop_words: str | None,
    labels: str | None,
):
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: (%(name)s) %(message)s",
    )

    df = load_datasets(inputs, splits=split, sample=sample)

    print(df)

    if enable_projection and (x_column is None or y_column is None):
        # No x, y column selected, first see if text/image/vectors column is specified, if not, ask for it
        if text is None and image is None and vector is None:
            text = prompt_for_column(
                df, "Select a column you want to run the embedding on"
            )
        umap_args = {}
        if umap_min_dist is not None:
            umap_args["min_dist"] = umap_min_dist
        if umap_n_neighbors is not None:
            umap_args["n_neighbors"] = umap_n_neighbors
        if umap_random_state is not None:
            umap_args["random_state"] = umap_random_state
        if umap_metric is not None:
            umap_args["metric"] = umap_metric
        # Run embedding and projection
        if text is not None or image is not None or vector is not None:
            from .projection import (
                compute_image_projection,
                compute_text_projection,
                compute_vector_projection,
            )

            x_column = find_column_name(df.columns, "projection_x")
            y_column = find_column_name(df.columns, "projection_y")
            if neighbors_column is None:
                neighbors_column = find_column_name(df.columns, "__neighbors")
                new_neighbors_column = neighbors_column
            else:
                # If neighbors_column is already specified, don't overwrite it.
                new_neighbors_column = None
            if vector is not None:
                compute_vector_projection(
                    df,
                    vector,
                    x=x_column,
                    y=y_column,
                    neighbors=new_neighbors_column,
                    umap_args=umap_args,
                )
            elif text is not None:
                compute_text_projection(
                    df,
                    text,
                    x=x_column,
                    y=y_column,
                    neighbors=new_neighbors_column,
                    model=model,
                    trust_remote_code=trust_remote_code,
                    batch_size=batch_size,
                    umap_args=umap_args,
                )
            elif image is not None:
                compute_image_projection(
                    df,
                    image,
                    x=x_column,
                    y=y_column,
                    neighbors=new_neighbors_column,
                    model=model,
                    trust_remote_code=trust_remote_code,
                    batch_size=batch_size,
                    umap_args=umap_args,
                )
            else:
                raise RuntimeError("unreachable")

    id_column = find_column_name(df.columns, "_row_index")
    df[id_column] = range(df.shape[0])

    stop_words_resolved = None
    if stop_words is not None:
        stop_words_df = load_pandas_data(stop_words)
        stop_words_resolved = stop_words_df["word"].to_list()

    labels_resolved = None
    if labels is not None:
        labels_df = load_pandas_data(labels)
        labels_resolved = labels_df.to_dict("records")

    props = make_embedding_atlas_props(
        row_id=id_column,
        x=x_column,
        y=y_column,
        neighbors=neighbors_column,
        text=text,
        point_size=point_size,
        stop_words=stop_words_resolved,
        labels=labels_resolved,
    )

    metadata = {
        "props": props,
    }

    hasher = Hasher()
    hasher.update(__version__)
    hasher.update(inputs)
    hasher.update(metadata)
    identifier = hasher.hexdigest()

    dataset = DataSource(identifier, df, metadata)

    if static is None:
        static = str((pathlib.Path(__file__).parent / "static").resolve())

    if export_application is not None:
        with open(export_application, "wb") as f:
            f.write(dataset.make_archive(static))
        exit(0)

    app = make_server(dataset, static_path=static, duckdb_uri=duckdb)

    if enable_auto_port:
        new_port = find_available_port(port, max_attempts=10, host=host)
        if new_port != port:
            logging.info(f"Port {port} is not available, using {new_port}")
    else:
        new_port = port
    uvicorn.run(app, port=new_port, host=host, access_log=False)


@cli.command(name="export-hf")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--repo-id",
    required=True,
    help="Hugging Face repository ID (e.g., 'username/dataset-name')",
)
@click.option(
    "--private",
    is_flag=True,
    default=False,
    help="Create a private dataset (default: public)",
)
@click.option(
    "--token",
    default=None,
    envvar="HF_TOKEN",
    help="Hugging Face API token (or set HF_TOKEN environment variable)",
)
@click.option(
    "--commit-message",
    default=None,
    help="Custom commit message (default: 'Upload embedding atlas dataset')",
)
@click.option(
    "--create-pr",
    is_flag=True,
    default=False,
    help="Create a pull request instead of committing directly",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be uploaded without actually uploading",
)
def export_hf(
    input_file: str,
    repo_id: str,
    private: bool,
    token: str | None,
    commit_message: str | None,
    create_pr: bool,
    dry_run: bool,
):
    """Export an embedding atlas dataset to Hugging Face Hub.

    INPUT_FILE should be a .parquet file containing the atlas data with
    required columns: projection_x, projection_y, _row_index, and optionally __neighbors.

    Examples:

      \b
      # Export to a public dataset
      embedding-atlas export-hf my-atlas.parquet --repo-id username/my-atlas

      \b
      # Export to a private dataset with token
      embedding-atlas export-hf my-atlas.parquet \\
        --repo-id username/my-atlas \\
        --private \\
        --token hf_...

      \b
      # Create a pull request instead of direct commit
      embedding-atlas export-hf my-atlas.parquet \\
        --repo-id username/my-atlas \\
        --create-pr
    """
    import os
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Load the parquet file
        click.echo(f"Loading data from {input_file}...")
        df = load_pandas_data(input_file)

        # Validate required columns
        required_cols = ["projection_x", "projection_y", "_row_index"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            click.echo(
                f"Error: Missing required columns: {', '.join(missing_cols)}",
                err=True,
            )
            click.echo(
                "\nRequired columns for HF export:",
                err=True,
            )
            click.echo("  - projection_x: X coordinate of 2D projection", err=True)
            click.echo("  - projection_y: Y coordinate of 2D projection", err=True)
            click.echo("  - _row_index: Unique row identifier", err=True)
            click.echo(
                "\nOptional but recommended:",
                err=True,
            )
            click.echo(
                "  - __neighbors: Pre-computed K-nearest neighbors",
                err=True,
            )
            sys.exit(1)

        # Create DataSource with metadata
        # Try to detect text column for metadata
        text_col = None
        for col in df.columns:
            if col not in required_cols and df[col].dtype == "object":
                text_col = col
                break

        props = make_embedding_atlas_props(
            row_id="_row_index",
            x="projection_x",
            y="projection_y",
            neighbors="__neighbors" if "__neighbors" in df.columns else None,
            text=text_col,
        )

        metadata = {"props": props}

        hasher = Hasher()
        hasher.update(__version__)
        hasher.update([input_file])
        hasher.update(metadata)
        identifier = hasher.hexdigest()

        data_source = DataSource(identifier, df, metadata)

        if dry_run:
            click.echo("\n=== DRY RUN ===")
            click.echo(f"Would upload to: https://huggingface.co/datasets/{repo_id}")
            click.echo(f"Dataset size: {len(df):,} rows")
            click.echo(f"Columns: {list(df.columns)}")
            click.echo(f"Private: {private}")
            click.echo(f"Create PR: {create_pr}")
            if commit_message:
                click.echo(f"Commit message: {commit_message}")
            click.echo("\nFiles that would be uploaded:")
            click.echo("  - dataset.parquet")
            click.echo("  - metadata.json")
            click.echo("  - README.md")
            if data_source.cache_path.exists():
                cache_files = list(data_source.cache_path.glob("*.json"))
                if cache_files:
                    click.echo(f"  - cache/*.json ({len(cache_files)} files)")
            click.echo("\nNo files were uploaded (dry run).")
            return

        # Check authentication
        if token is None:
            if "HF_TOKEN" not in os.environ:
                click.echo(
                    "Error: No Hugging Face token provided. Set --token or HF_TOKEN environment variable.",
                    err=True,
                )
                sys.exit(1)

        # Upload to HF
        click.echo(f"\nUploading to Hugging Face: {repo_id}")
        click.echo(f"Privacy: {'Private' if private else 'Public'}")

        url = data_source.push_to_hub(
            repo_id=repo_id,
            private=private,
            token=token,
            commit_message=commit_message,
            create_pr=create_pr,
        )

        click.echo(f"\n✓ Successfully uploaded to: {url}")

        if create_pr:
            click.echo(
                "\nA pull request was created. Visit the URL above to review and merge it."
            )
        else:
            click.echo("\nYou can now:")
            click.echo(f"  - View the dataset: {url}")
            click.echo(f"  - Load in Python: embedding-atlas from-hf {repo_id}")
            click.echo(
                f"  - Create static viewer: embedding-atlas generate-static-viewer --source hf://datasets/{repo_id}"
            )

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback

        if logging.getLogger().level == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


# Keep backward compatibility with old entry point
def main():
    """Legacy entry point for backward compatibility."""
    cli(prog_name="embedding-atlas")


if __name__ == "__main__":
    cli()
