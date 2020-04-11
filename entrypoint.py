#!/usr/bin/env python3

import sys
from datetime import datetime
import argparse

def main(who_to_greet):
    print(f"Hello {who_to_greet} from Python")
    time = datetime.now().isoformat()
    print(f"::set-output name=time::{time}")


def parse_args():
    parser = argparse.ArgumentParser(description='Greetings')
    parser.add_argument('who_to_greet', help='Who to greet', nargs="?", default="World")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    who_to_greet = args.who_to_greet
    main(who_to_greet)
