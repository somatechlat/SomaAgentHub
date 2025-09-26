#!/usr/bin/env python3
"""
Seed loader for model_profiles.

Usage:
  ./scripts/seed_model_profiles.py --write-json infra/seeds/model_profiles.json
  ./scripts/seed_model_profiles.py --dry-run

Optional (not executed by default): --apply to POST to settings-service endpoint

This script is intentionally self-contained and uses PyYAML and requests when needed.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_schema(data: dict):
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be a mapping")
    if "profiles" not in data or not isinstance(data["profiles"], list):
        raise ValueError("YAML must contain a 'profiles' list")
    # minimal per-profile checks
    for p in data["profiles"]:
        if "role" not in p or "primary" not in p:
            raise ValueError(f"profile missing required fields: {p}")


def convert_to_seed(data: dict) -> dict:
    return {
        "metadata": {
            "source": "docs/slm_profiles.yaml"
        },
        "profiles": data.get("profiles", []),
    }


def write_json(obj: dict, outpath: Path):
    with outpath.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False)
    print(f"Wrote JSON seed to {outpath}")


async def upsert_postgres(seed: dict):
    """
    Perform a real DB upsert using asyncpg.
    """
    import os
    import asyncpg
    # Use POSTGRES_URL if provided, otherwise fall back to defaults.
    dsn = os.getenv("POSTGRES_URL")
    if dsn:
        conn = await asyncpg.connect(dsn)
    else:
        conn = await asyncpg.connect(
            host="localhost",
            database="model_profiles",
            user="postgres",
            password="password",
        )
    for profile in seed["profiles"]:
        await conn.execute(
            "INSERT INTO profiles (role, primary) VALUES ($1, $2) ON CONFLICT DO UPDATE SET primary = $2",
            profile["role"],
            profile["primary"],
        )
    await conn.close()


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", default="docs/slm_profiles.yaml", help="source YAML")
    parser.add_argument("--write-json", help="path to write JSON seed file")
    parser.add_argument("--dry-run", action="store_true", help="validate and print summary")
    parser.add_argument("--apply", action="store_true", help="(placeholder) post to settings-service API")
    args = parser.parse_args(argv)

    yaml_path = Path(args.yaml)
    if not yaml_path.exists():
        print(f"YAML file not found: {yaml_path}")
        return 2

    data = load_yaml(yaml_path)
    try:
        validate_schema(data)
    except Exception as e:
        print(f"Validation error: {e}")
        return 3

    seed = convert_to_seed(data)

    if args.dry_run:
        print("Dry run OK — profiles:")
        for p in seed["profiles"]:
            print(f" - {p.get('role')} (primary={p.get('primary')})")

    if args.write_json:
        outpath = Path(args.write_json)
        outpath.parent.mkdir(parents=True, exist_ok=True)
        write_json(seed, outpath)

    if args.apply:
        # Perform a real DB upsert using asyncpg.
        try:
            asyncio.run(upsert_postgres(seed))
        except Exception as e:
            print(f"Error during DB upsert: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
