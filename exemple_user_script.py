#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators, absolute_import
""" THIS IS AN EXEMPLE """


from socialism.param_serv.param_utils import *
from socialism import client

def main():
    soc = client.Client()
    soc["test"] = -np.ones((10, 20, 30))
    soc["test"][2:5, 2:5, 2:5] = np.zeros((3, 3, 3))
    soc.pull_full("test")
    soc.push_as_part("test", [[0], [1, 4], [1, 6]], 1, 1)
    soc["test"] *= 2


if __name__ == "__main__":
    main()