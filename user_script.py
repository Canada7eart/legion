#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import sys, argparse

from param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc["test"] = -np.ones(soc["test"].shape)
    soc.push_full("test", 0, 1)
    soc["test"] = np.ones(soc["test"].shape)
    soc.pull_part("test", ((1, 2, 4), (2, 3, 9)))
    print(soc.get("test"))

    print("user script - done")

if __name__ == "__main__":
    main()