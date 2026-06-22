#!/usr/bin/env python3
"""
PDF Summary Assistant - CLI entry point.

Usage:
    python main.py "Summarize the file report.pdf"
    python main.py                        # Interactive mode
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_summary_agent.agent import run_agent, interactive_session


def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        try:
            result = run_agent(query)
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        interactive_session()


if __name__ == "__main__":
    main()
