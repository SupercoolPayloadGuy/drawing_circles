"""
cli.py — command-line argument parsing.
"""

import argparse


def parse_args():
    p = argparse.ArgumentParser(description="Circle Construction")
    p.add_argument("-p", "--points", type=int, default=0,
                   help="Number of base points (overrides intro selection)")
    return p.parse_args()
