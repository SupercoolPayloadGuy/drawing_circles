"""
cli.py — command-line argument parsing.
"""

import argparse


def parse_args():
    p = argparse.ArgumentParser(description="Triangle Construction")
    p.add_argument("-g", "--generations", type=int, default=0,
                   help="Number of generations (overrides intro selection)")
    return p.parse_args()
