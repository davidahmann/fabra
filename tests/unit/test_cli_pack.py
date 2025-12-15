from __future__ import annotations

import json
import zipfile

from typer.testing import CliRunner

from fabra.cli import app
from fabra.receipts import ReceiptRecorder


runner = CliRunner()


def test_context_pack_local_writes_zip_with_expected_files(tmp_path) -> None:
    duckdb_path = tmp_path / "receipts.duckdb"
    recorder = ReceiptRecorder(duckdb_path=str(duckdb_path))

    base = recorder.record_sync(
        context_function="unit_test",
        content="system: hello\nuser: base\n",
        inputs={"k": "base"},
    )
    newer = recorder.record_sync(
        context_function="unit_test",
        content="system: hello\nuser: newer\n",
        inputs={"k": "newer"},
    )

    output_zip = tmp_path / "incident.zip"
    result = runner.invoke(
        app,
        [
            "context",
            "pack",
            newer.context_id,
            "--baseline",
            base.context_id,
            "--local",
            "--duckdb-path",
            str(duckdb_path),
            "--output",
            str(output_zip),
        ],
    )
    assert result.exit_code == 0, result.stdout

    with zipfile.ZipFile(output_zip, "r") as zf:
        names = set(zf.namelist())
        assert "context.json" in names
        assert "summary.md" in names
        assert "diff.patch" in names

        context_obj = json.loads(zf.read("context.json").decode("utf-8"))
        assert context_obj["context_id"] == newer.context_id

        summary = zf.read("summary.md").decode("utf-8")
        assert newer.context_id in summary
        assert base.context_id in summary

        diff_patch = zf.read("diff.patch").decode("utf-8")
        assert diff_patch.startswith("--- ")
        assert "+user: newer" in diff_patch


def test_context_pack_local_without_baseline_has_no_diff_patch(tmp_path) -> None:
    duckdb_path = tmp_path / "receipts.duckdb"
    recorder = ReceiptRecorder(duckdb_path=str(duckdb_path))
    receipt = recorder.record_sync(
        context_function="unit_test",
        content="system: hello\nuser: only\n",
    )

    output_zip = tmp_path / "incident.zip"
    result = runner.invoke(
        app,
        [
            "context",
            "pack",
            receipt.context_id,
            "--local",
            "--duckdb-path",
            str(duckdb_path),
            "--output",
            str(output_zip),
        ],
    )
    assert result.exit_code == 0, result.stdout

    with zipfile.ZipFile(output_zip, "r") as zf:
        names = set(zf.namelist())
        assert "context.json" in names
        assert "summary.md" in names
        assert "diff.patch" not in names
