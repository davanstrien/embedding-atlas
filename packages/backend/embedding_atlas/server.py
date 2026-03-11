# Copyright (c) 2025 Apple Inc. Licensed under MIT License.

import asyncio
import concurrent.futures
import json
import os
import re
import uuid
from functools import lru_cache
from typing import Callable

import duckdb
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .data_source import DataSource
from .utils import arrow_to_bytes, to_parquet_bytes


def make_server(
    data_source: DataSource | None,
    *,
    static_path: str,
    mcp: bool = False,
    cors: bool | list[str] = False,
    duckdb_uri: str | None = None,
    dataset_url: str | None = None,
    hf_token: str | None = None,
    metadata: dict | None = None,
):
    """Creates a server for hosting Embedding Atlas"""

    app = FastAPI()

    if cors is not None:
        if isinstance(cors, bool) and cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
                expose_headers=["*"],
            )
        elif isinstance(cors, list):
            app.add_middleware(
                CORSMiddleware,
                allow_origins=cors,
                allow_methods=["*"],
                allow_headers=["*"],
                expose_headers=["*"],
            )

    if data_source is not None:
        mount_bytes(
            app,
            "/data/dataset.parquet",
            "application/octet-stream",
            lambda: to_parquet_bytes(data_source.dataset),
        )

    @app.get("/data/metadata.json")
    async def get_metadata():
        meta = {}
        # Database
        if duckdb_uri is None or duckdb_uri == "wasm":
            meta["database"] = {"type": "wasm", "load": True}
        elif duckdb_uri == "server":
            # Point to the server itself.
            meta["database"] = {"type": "rest"}
        else:
            # Point to the given uri.
            if duckdb_uri.startswith("http"):
                meta["database"] = {
                    "type": "rest",
                    "uri": duckdb_uri,
                    "load": True,
                }
            elif duckdb_uri.startswith("ws"):
                meta["database"] = {
                    "type": "socket",
                    "uri": duckdb_uri,
                    "load": True,
                }
            else:
                raise ValueError("invalid DuckDB uri")
        # MCP
        if mcp:
            meta["mcp"] = {"type": "websocket"}

        base_metadata = (
            data_source.metadata if data_source is not None else (metadata or {})
        )
        return base_metadata | meta

    @app.post("/data/cache/{name}")
    async def post_cache(request: Request, name: str):
        if data_source is None:
            return Response(status_code=501)
        data_source.cache_set(name, await request.json())

    @app.get("/data/cache/{name}")
    async def get_cache(name: str):
        if data_source is None:
            return Response(status_code=404)
        obj = data_source.cache_get(name)
        if obj is None:
            return Response(status_code=404)
        return obj

    @app.get("/data/archive.zip")
    async def make_archive():
        if data_source is None:
            return Response(status_code=501)
        data = data_source.make_archive(static_path)
        return Response(content=data, media_type="application/zip")

    if duckdb_uri == "server":
        if dataset_url is not None:
            duckdb_connection = make_duckdb_connection(
                dataset_url=dataset_url, hf_token=hf_token
            )
        elif data_source is not None:
            duckdb_connection = make_duckdb_connection(data_source.dataset)
        else:
            duckdb_connection = None
    else:
        duckdb_connection = None

    def handle_query(query: dict):
        assert duckdb_connection is not None
        sql = query["sql"]
        command = query["type"]
        with duckdb_connection.cursor() as cursor:
            try:
                result = cursor.execute(sql)
                if command == "exec":
                    return JSONResponse({})
                elif command == "arrow":
                    buf = arrow_to_bytes(result.arrow())
                    return Response(
                        buf, headers={"Content-Type": "application/octet-stream"}
                    )
                elif command == "json":
                    data = result.df().to_json(orient="records")
                    return Response(data, headers={"Content-Type": "application/json"})
                else:
                    raise ValueError(f"Unknown command {command}")
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

    def handle_selection(query: dict):
        assert duckdb_connection is not None
        predicate = query.get("predicate", None)
        format = query["format"]
        formats = {
            "json": "(FORMAT JSON, ARRAY true)",
            "jsonl": "(FORMAT JSON)",
            "csv": "(FORMAT CSV)",
            "parquet": "(FORMAT parquet)",
        }
        with duckdb_connection.cursor() as cursor:
            filename = ".selection-" + str(uuid.uuid4()) + ".tmp"
            try:
                if predicate is not None:
                    cursor.execute(
                        f"COPY (SELECT * FROM dataset WHERE {predicate}) TO '{filename}' {formats[format]}"
                    )
                else:
                    cursor.execute(f"COPY dataset TO '{filename}' {formats[format]}")
                with open(filename, "rb") as f:
                    buffer = f.read()
                    return Response(
                        buffer, headers={"Content-Type": "application/octet-stream"}
                    )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
            finally:
                try:
                    os.unlink(filename)
                except Exception:
                    pass

    executor = concurrent.futures.ThreadPoolExecutor()

    @app.get("/data/query")
    async def get_query(req: Request):
        data = json.loads(req.query_params["query"])
        return await asyncio.get_running_loop().run_in_executor(
            executor, lambda: handle_query(data)
        )

    @app.post("/data/query")
    async def post_query(req: Request):
        body = await req.body()
        data = json.loads(body)
        return await asyncio.get_running_loop().run_in_executor(
            executor, lambda: handle_query(data)
        )

    @app.post("/data/selection")
    async def post_selection(req: Request):
        body = await req.body()
        data = json.loads(body)
        return await asyncio.get_running_loop().run_in_executor(
            executor, lambda: handle_selection(data)
        )

    if mcp:
        make_mcp_proxy(app)

    # Static files for the frontend
    app.mount("/", StaticFiles(directory=static_path, html=True))

    return app


class WebSocketHandler:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.is_connected = True

    async def handle_connection(self):
        try:
            while self.is_connected:
                data = await self.websocket.receive_text()
                await self._handle_message(data)
        except Exception as _:
            pass
        finally:
            await self._cleanup()

    async def _handle_message(self, data: str):
        try:
            response = json.loads(data)
            request_id = response.get("id")
            if request_id and request_id in self.pending_requests:
                future = self.pending_requests.pop(request_id)
                if not future.done():
                    future.set_result(response.get("response"))
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")

    async def _cleanup(self):
        self.is_connected = False
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()

    async def send_request(self, request: dict) -> dict:
        """Send a request to the WebSocket and wait for response"""
        if not self.is_connected:
            raise HTTPException(status_code=503, detail="WebSocket disconnected")

        request_id = str(uuid.uuid4())
        payload = {"id": request_id, "request": request}

        future = asyncio.Future()
        self.pending_requests[request_id] = future

        try:
            await self.websocket.send_text(json.dumps(payload))
            response = await asyncio.wait_for(future, timeout=30.0)
            return response

        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise HTTPException(status_code=408, detail="Request timeout")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            if not self.is_connected:
                raise HTTPException(status_code=503, detail="WebSocket disconnected")
            else:
                raise HTTPException(
                    status_code=500, detail=f"Internal server error: {str(e)}"
                )

    async def send_close(self):
        try:
            await self.websocket.send_text(json.dumps({"control": "close"}))
        except Exception:
            pass


def make_mcp_proxy(app: FastAPI):
    # Registry to track the last connected WebSocket handler
    last_handler: dict[str, WebSocketHandler | None] = {"handler": None}

    @app.websocket("/data/mcp_websocket")
    async def websocket_mcp_ws(websocket: WebSocket):
        await websocket.accept()

        # Create a new handler for this WebSocket connection
        handler = WebSocketHandler(websocket)
        if last_handler["handler"] is not None:
            # Tell the existing client to close.
            await last_handler["handler"].send_close()
        last_handler["handler"] = handler

        # Handle the connection (this will block until disconnection)
        await handler.handle_connection()

        # Clear the handler if it was the last one
        if last_handler["handler"] == handler:
            last_handler["handler"] = None

    @app.post("/mcp")
    async def post_mcp(request: Request):
        # Check if we have a connected WebSocket handler
        handler = last_handler["handler"]
        if handler is None or not handler.is_connected:
            raise HTTPException(status_code=503, detail="No MCP WebSocket connected")

        return await handler.send_request(await request.json())


def make_duckdb_connection(df=None, *, dataset_url=None, hf_token=None):
    con = duckdb.connect(":memory:")
    if dataset_url is not None:
        if not dataset_url.startswith("https://"):
            raise ValueError("--dataset-url must be an HTTPS URL")
        con.sql("INSTALL httpfs")
        con.sql("LOAD httpfs")
        if hf_token:
            con.execute(
                "SET http_extra_headers = MAP {'Authorization': ?}",
                [f"Bearer {hf_token}"],
            )
        safe_url = dataset_url.replace("'", "''")
        con.sql(f"CREATE TABLE dataset AS (SELECT * FROM read_parquet('{safe_url}'))")
        # Ensure __row_index__ exists for the frontend
        cols = [row[0] for row in con.sql("DESCRIBE dataset").fetchall()]
        if "__row_index__" not in cols:
            con.sql(
                "CREATE TABLE _tmp AS SELECT *, "
                "(row_number() OVER () - 1)::INTEGER AS __row_index__ "
                "FROM dataset"
            )
            con.sql("DROP TABLE dataset")
            con.sql("ALTER TABLE _tmp RENAME TO dataset")
    else:
        _ = df  # used in the query
        con.sql("CREATE TABLE dataset AS (SELECT * FROM df)")
    con.sql("SET enable_external_access = false")
    con.sql("SET lock_configuration = true")
    return con


def parse_range_header(request: Request, content_length: int):
    value = request.headers.get("Range")
    if value is not None:
        m = re.match(r"^ *bytes *= *([0-9]+) *- *([0-9]+) *$", value)
        if m is not None:
            r0 = int(m.group(1))
            r1 = int(m.group(2)) + 1
            if r0 < r1 and r0 <= content_length and r1 <= content_length:
                return (r0, r1)
    return None


def mount_bytes(
    app: FastAPI, url: str, media_type: str, make_content: Callable[[], bytes]
):
    @lru_cache(maxsize=1)
    def get_content() -> bytes:
        return make_content()

    @app.head(url)
    async def head(request: Request):
        content = get_content()
        bytes_range = parse_range_header(request, len(content))
        if bytes_range is None:
            length = len(content)
        else:
            length = bytes_range[1] - bytes_range[0]
        return Response(
            headers={
                "Content-Length": str(length),
                "Content-Type": media_type,
            }
        )

    @app.get(url)
    async def get(request: Request):
        content = get_content()
        bytes_range = parse_range_header(request, len(content))
        if bytes_range is None:
            return Response(content=content)
        else:
            r0, r1 = bytes_range
            result = content[r0:r1]
            return Response(
                content=result,
                headers={
                    "Content-Length": str(r1 - r0),
                    "Content-Range": f"bytes {r0}-{r1 - 1}/{len(content)}",
                    "Content-Type": media_type,
                },
                media_type=media_type,
                status_code=206,
            )
