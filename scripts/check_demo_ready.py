"""Read-only preflight checks for the BehavePass final-review demo."""

from __future__ import annotations

import hashlib
import math
import shutil
import socket
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CHECKPOINT_PATH = PROJECT_ROOT / "ml" / "checkpoints" / "fusion_bilstm.pt"
PREPROCESSING_PATH = PROJECT_ROOT / "ml" / "results" / "sequence_preprocessing.json"
EXPECTED_CHECKPOINT_SHA256 = (
    "e7df2f6d14c0b36ba764de1243c69cdd101418087945fd1103459d40184a34a5"
)
EXPECTED_PREPROCESSING_SHA256 = (
    "f6f034fe512838ed31c50f0957e5328584b7bca62bf7130bc9d2ae7df76cced2"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report(label: str, passed: bool, detail: str = "") -> bool:
    suffix = f" - {detail}" if detail else ""
    print(f"{label}: {'PASS' if passed else 'FAIL'}{suffix}")
    return passed


def port_is_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def main() -> int:
    print("## BehavePass Demo Readiness\n")
    results: list[bool] = []
    backend_imports_ok = False

    required_paths = [
        BACKEND_DIR / "app" / "main.py",
        BACKEND_DIR / "requirements.txt",
        FRONTEND_DIR / "package.json",
        FRONTEND_DIR / "package-lock.json",
        PROJECT_ROOT / "ml" / "sequence" / "models.py",
    ]
    results.append(report("Required files", all(path.is_file() for path in required_paths)))
    results.append(report("Checkpoint", CHECKPOINT_PATH.is_file(), str(CHECKPOINT_PATH)))
    results.append(
        report("Preprocessing metadata", PREPROCESSING_PATH.is_file(), str(PREPROCESSING_PATH))
    )

    checksum_ok = False
    if CHECKPOINT_PATH.is_file():
        actual_checksum = sha256(CHECKPOINT_PATH)
        checksum_ok = actual_checksum == EXPECTED_CHECKPOINT_SHA256
        results.append(report("Checkpoint SHA-256", checksum_ok, actual_checksum))
    else:
        results.append(report("Checkpoint SHA-256", False, "checkpoint unavailable"))

    metadata_checksum_ok = False
    if PREPROCESSING_PATH.is_file():
        metadata_checksum = sha256(PREPROCESSING_PATH)
        metadata_checksum_ok = metadata_checksum == EXPECTED_PREPROCESSING_SHA256
        results.append(report("Preprocessing SHA-256", metadata_checksum_ok, metadata_checksum))
    else:
        results.append(report("Preprocessing SHA-256", False, "metadata unavailable"))

    node_ok = shutil.which("node") is not None
    frontend_dependencies_ok = (FRONTEND_DIR / "node_modules" / "vite" / "package.json").is_file()
    results.append(report("Node.js", node_ok))
    results.append(
        report(
            "Frontend dependencies",
            frontend_dependencies_ok,
            "run npm install in frontend" if not frontend_dependencies_ok else "installed",
        )
    )
    results.append(report("Backend port 8000", port_is_available(8000), "available"))
    results.append(report("Frontend port 5173", port_is_available(5173), "available"))

    sys.path.insert(0, str(BACKEND_DIR))
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        import sqlite3

        import torch
        from app.api.predict import prototype_predict  # noqa: F401
        from app.core.config import settings
        from app.ml.inference import get_fusion_inference
        from app.schemas.session import (
            CreateSessionPayload,
            KeystrokeFeatureItem,
            PredictRequest,
            StaticFeaturesSchema,
        )

        sqlite3.connect(":memory:").close()
        backend_imports_ok = True
        results.append(report("Backend imports", True, f"PyTorch {torch.__version__}"))
        results.append(
            report(
                "SQLite configuration",
                settings.DATABASE_URL.startswith("sqlite"),
                "no external database required",
            )
        )

        forbidden = {"password", "plaintext", "raw_keys", "key_char"}
        schema_fields = set(CreateSessionPayload.model_fields) | set(PredictRequest.model_fields)
        privacy_ok = not (schema_fields & forbidden)
        results.append(report("Privacy configuration", privacy_ok, "derived features only"))

        if checksum_ok and metadata_checksum_ok:
            get_fusion_inference.cache_clear()
            inference = get_fusion_inference()
            cached = get_fusion_inference()
            sequence = [
                KeystrokeFeatureItem(
                    sequence_index=index,
                    dwell_time=85.0 + index,
                    flight_time=None if index == 0 else 70.0 + index,
                    press_to_press_latency=None if index == 0 else 155.0 + index,
                    is_backspace=False,
                    is_pause=False,
                )
                for index in range(8)
            ]
            static = StaticFeaturesSchema(
                password_length=8,
                lowercase_count=4,
                uppercase_count=1,
                digit_count=2,
                symbol_count=1,
                unique_character_count=8,
                repeated_character_count=0,
                repeated_substring_count=0,
                sequential_character_count=0,
                zxcvbn_score=3,
                log10_estimated_guesses=7.0,
                empirical_character_entropy=3.0,
                character_pool_entropy_estimate=52.0,
            )
            first = inference.predict(sequence, static)
            second = inference.predict(sequence, static)
            with torch.no_grad():
                normalized = inference.model(
                    inference.preprocess_sequence(sequence).unsqueeze(0),
                    torch.tensor([len(sequence)], dtype=torch.long),
                    inference.preprocess_static(static).unsqueeze(0),
                ).item()
            denormalized = normalized * inference.target_std + inference.target_mean
            inference_ok = (
                math.isfinite(first)
                and first == second
                and math.isclose(first, denormalized, rel_tol=0.0, abs_tol=1e-7)
                and cached is inference
                and get_fusion_inference.cache_info().misses == 1
                and not hasattr(inference, "fit")
            )
            results.append(report("Model load", True, "CPU evaluation mode"))
            results.append(
                report(
                    "Inference consistency",
                    inference_ok,
                    f"prediction={first:.6f}; cached instance reused",
                )
            )
        else:
            results.append(report("Model load", False, "artifact verification failed"))
            results.append(report("Inference consistency", False, "model not loaded"))
    except Exception as error:
        results.append(report("Backend imports/model load", False, str(error)))

    config_text = (BACKEND_DIR / "app" / "main.py").read_text(encoding="utf-8")
    vite_text = (FRONTEND_DIR / "vite.config.ts").read_text(encoding="utf-8")
    runtime_config_ok = (
        "CORSMiddleware" in config_text
        and "port: 5173" in vite_text
        and "http://127.0.0.1:8000" in vite_text
    )
    results.append(report("Runtime configuration", runtime_config_ok, "frontend 5173 -> backend 8000"))

    ready = all(results) and backend_imports_ok
    print(f"\n{'DEMO READY' if ready else 'DEMO NOT READY'}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
