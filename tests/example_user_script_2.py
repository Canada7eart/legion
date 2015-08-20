#!/usr/bin/env python2
from __future__ import print_function, division, with_statement

""" THIS IS AN EXEMPLE """

import sys, argparse, os, re

import numpy as np
from legion import Client

def main():
    legion = Client()

    parser = argparse.ArgumentParser()
    parser.add_argument("--arg0", default=False, action="store_true")
    parser.add_argument("--arg1", default=False, action="store_true")

    parser.add_argument("--the_str", default="whatever", type=str)

    print(parser.parse_args())

if __name__ == "__main__":
    main()
