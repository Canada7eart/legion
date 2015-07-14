#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import sys, argparse

from param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc.pull_full("test")
    print(soc.get("test"))

    soc["test"] = np.random.random(soc["test"].shape)
    soc.push_full("test", 0.5, 0.5)
    soc.pull_full("test")
    print(soc.get("test"))

    print("user script - done")

if __name__ == "__main__":
    main()