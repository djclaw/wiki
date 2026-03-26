#!/usr/bin/env python3
"""Compatibility wrapper.
The wiki extraction PoC has been promoted into the main extraction module.
Use history_extraction.py for the canonical implementation.
"""
from history_extraction import *  # noqa: F401,F403

if __name__ == '__main__':
    raise SystemExit(main())
