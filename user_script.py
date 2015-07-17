#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import sys, argparse

from param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc["test"] = -np.ones((10, 10))
    soc.create_if_doesnt_exist("test")
    soc["test"][2:5, 2:5] = np.zeros((3, 3))
    soc.pull_from_indices("test", [(2, 2), (3, 3), (4, 4)])
    print(soc.get("test"))

    print("user script - done")

if __name__ == "__main__":
    main()