"""Batch bridge to the existing frontend static-feature implementation."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from .schemas import StaticFeatures


class FrontendStaticFeatureError(RuntimeError):
    pass


def extract_frontend_static_features(
    passwords: set[str], frontend_dir: Path | None = None
) -> dict[str, StaticFeatures]:
    if not passwords:
        return {}
    project_root = Path(__file__).resolve().parents[2]
    frontend = (frontend_dir or project_root / "frontend").resolve()
    if not (frontend / "src" / "utils" / "staticFeatures.ts").is_file():
        raise FrontendStaticFeatureError(f"frontend static extractor not found under {frontend}")
    script = """
import fs from 'node:fs';
import { createServer } from 'vite';
import zxcvbn from 'zxcvbn';
const passwords = JSON.parse(fs.readFileSync(0, 'utf8'));
const server = await createServer({
  logLevel: 'error',
  server: { middlewareMode: true },
  appType: 'custom'
});
try {
  const module = await server.ssrLoadModule('/src/utils/staticFeatures.ts');
  const output = passwords.map(password => {
    const features = module.calculateStaticFeatures(password);
    const guesses = Number(zxcvbn(password).guesses || 1);
    return { password, features, guesses };
  });
  process.stdout.write(JSON.stringify(output));
} finally {
  await server.close();
}
"""
    try:
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            input=json.dumps(sorted(passwords)),
            text=True,
            capture_output=True,
            cwd=frontend,
            check=False,
        )
    except OSError as error:
        raise FrontendStaticFeatureError(f"could not launch Node.js: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unknown error"
        raise FrontendStaticFeatureError(f"frontend static extraction failed: {detail}")
    try:
        rows = json.loads(completed.stdout.strip().splitlines()[-1])
    except json.JSONDecodeError as error:
        raise FrontendStaticFeatureError("frontend static extractor returned invalid JSON") from error

    output: dict[str, StaticFeatures] = {}
    for row in rows:
        values = row["features"]
        guesses = float(row["guesses"])
        output[row["password"]] = StaticFeatures(
            password_length=values["password_length"],
            lowercase_count=values["lowercase_count"],
            uppercase_count=values["uppercase_count"],
            digit_count=values["digit_count"],
            symbol_count=values["symbol_count"],
            unique_character_count=values["unique_character_count"],
            repeated_character_count=values["repeated_character_count"],
            repeated_substring_count=values["repeated_substring_count"],
            sequential_character_count=values["sequential_character_count"],
            zxcvbn_score=values["zxcvbn_score"],
            guess_count=guesses,
            # Match frontend calculateStaticFeatures exactly.
            log10_guesses=math.log10(max(guesses, 1.0) + 1.0),
            empirical_character_entropy=values["empirical_character_entropy"],
            character_pool_entropy_estimate=values["character_pool_entropy_estimate"],
        )
    return output
