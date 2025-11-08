#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio  # noqa: E402

from slm.adapters.selector import select_and_call  # noqa: E402


async def run():
    res = await select_and_call("hello world", {"role": "dialogue_reasoning"})
    print("adapter result:", res)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
