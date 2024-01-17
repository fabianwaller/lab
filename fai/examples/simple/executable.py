#!/usr/bin/env python3

print("Running dummy executable")

import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("fname", type=str, help="path of input file")
args = parser.parse_args()

print("Printing input file")
with open(args.fname, 'r') as fin:
    print(fin.read(), end="")
    #time.sleep(1)
    print("Done")

