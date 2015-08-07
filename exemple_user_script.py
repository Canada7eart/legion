#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators, absolute_import
""" THIS IS AN EXEMPLE """


from socialism.param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc["test"] = -np.ones((10, 10))
    soc["test"][2:5, 2:5] = np.zeros((3, 3))
    soc.push_from_indices("test", [[2, 3], [3, 3], [4, 3]], 0, 1)
    soc["test"] = -np.ones((10, 10))
    soc.pull_full("test")
    soc.pull_part("test", [[0], [1, 4]])
    soc.push_as_part("test", [[0], [1, 4]], 1, 1)
    soc["test"] *= 2

    print("Result:")
    print(soc.get("test"))
    print("user script - done")

if __name__ == "__main__":
    main()