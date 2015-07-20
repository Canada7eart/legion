#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators

from param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc["test"] = -np.ones((10, 10))
    soc.create_if_doesnt_exist("test")
    soc["test"][2:5, 2:5] = np.ones((3, 3))
    soc.push_from_indices("test", [[2, 3], [3, 3], [4, 3]], 0, 1)
    soc["test"] = -np.ones((10, 10))
    soc.pull_full("test")

    print("Result:")
    print(soc.get("test"))
    print("user script - done")

if __name__ == "__main__":
    main()