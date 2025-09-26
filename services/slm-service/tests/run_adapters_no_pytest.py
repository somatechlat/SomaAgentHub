#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from slm.adapters.selector import select_and_call
import asyncio


async def run():
    res = await select_and_call("hello world", {"role": "dialogue_reasoning"})
    print("adapter result:", res)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
