#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import subprocess  # nosec B404
import sys
import time
import urllib.request
import urllib.error
import zipfile
from pathlib import Path


def _wait_for_health(port: int, timeout_s: float = 30.0) -> None:
    url = f"http://127.0.0.1:{port}/health"
    start = time.time()
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # nosec B310
                if resp.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass
        if time.time() - start > timeout_s:
            raise RuntimeError(f"Timed out waiting for health endpoint: {url}")
        time.sleep(0.25)


def _post_context(port: int, user_id: str, query: str) -> str:
    url = f"http://127.0.0.1:{port}/v1/context/chat_context"
    payload = json.dumps({"user_id": user_id, "query": query}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
        data = json.loads(resp.read().decode("utf-8"))
    ctx_id = data.get("id")
    if not isinstance(ctx_id, str) or not ctx_id:
        raise RuntimeError(f"Missing context id in response: {data}")
    return ctx_id


def main() -> int:
    port = int(
        os.getenv("FABRA_BUNDLE_SMOKE_PORT", str(20000 + secrets.randbelow(10000)))
    )
    duckdb_path = os.getenv(
        "FABRA_BUNDLE_SMOKE_DUCKDB_PATH",
        str(Path.cwd() / f".fabra-bundle-{port}.duckdb"),
    )

    demo_cmd = [
        sys.executable,
        "-m",
        "fabra.cli",
        "demo",
        "--mode",
        "context",
        "--no-test",
        "--port",
        str(port),
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["FABRA_DUCKDB_PATH"] = duckdb_path

    proc: subprocess.Popen[str] | None = None
    bundle_path: Path | None = None
    try:
        proc = subprocess.Popen(demo_cmd, env=env)  # nosec B603
        _wait_for_health(port)

        ctx_id = _post_context(port, user_id="user_123", query="incident bundle smoke")
        bundle_path = Path.cwd() / f"{ctx_id}.zip"

        subprocess.run(
            [
                sys.executable,
                "-m",
                "fabra.cli",
                "context",
                "export",
                ctx_id,
                "--bundle",
                "--output",
                str(bundle_path),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            check=True,
        )  # nosec B603

        with zipfile.ZipFile(bundle_path) as zf:
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            if manifest.get("exported_kind") != "record":
                raise RuntimeError(
                    f"Expected CRS-001 record in bundle, got: {manifest}"
                )

            stored_record_hash = manifest.get("stored_record_hash")
            computed_record_hash = manifest.get("computed_record_hash")
            stored_content_hash = manifest.get("stored_content_hash")
            computed_content_hash = manifest.get("computed_content_hash")

            if not stored_record_hash or not computed_record_hash:
                raise RuntimeError(f"Missing record hashes in manifest: {manifest}")
            if not stored_content_hash or not computed_content_hash:
                raise RuntimeError(f"Missing content hashes in manifest: {manifest}")

            if stored_record_hash != computed_record_hash:
                raise RuntimeError(
                    f"record_hash mismatch: stored={stored_record_hash} computed={computed_record_hash}"
                )
            if stored_content_hash != computed_content_hash:
                raise RuntimeError(
                    f"content_hash mismatch: stored={stored_content_hash} computed={computed_content_hash}"
                )

        print(f"Bundle verified: {bundle_path}")
        return 0
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception as e:
                print(f"Warning: failed to terminate demo process: {e}")
                try:
                    proc.kill()
                except Exception as e2:
                    print(f"Warning: failed to kill demo process: {e2}")
        try:
            Path(duckdb_path).unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: failed to delete duckdb: {e}")
        if bundle_path:
            try:
                bundle_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Warning: failed to delete bundle: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
