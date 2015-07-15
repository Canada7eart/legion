#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import sys, argparse

from param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc.pull_full("test")
    print(soc.get("test"))

    soc["test"] = -np.ones(soc["test"].shape)
    soc.push_part("test", ((0, 1, 2, 3), (0, 1, 2, 3)), 0, 1)
    soc["test"] = np.zeros(soc["test"].shape)
    soc.pull_full("test")
    print(soc.get("test"))

    print("user script - done")

if __name__ == "__main__":
    main()