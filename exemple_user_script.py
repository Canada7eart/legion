#!/usr/bin/env python2
""" THIS IS AN EXEMPLE """

import numpy as np
from socialism import Client

def main():
    soc = Client()
    soc["test"] = -np.ones((10, 20, 30))
    soc["test"][2:5, 2:5, 2:5] = np.zeros((3, 3, 3))
    soc.pull_full("test")
    soc.push_as_part("test", [[0], [1, 4], [1, 6]], 1, 1)
    soc["test"] *= 2


if __name__ == "__main__":
    main()