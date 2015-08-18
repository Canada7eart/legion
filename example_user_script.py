#!/usr/bin/env python2
""" THIS IS AN EXEMPLE """

import numpy as np
from socialism import Client

def main():
    soc = Client()
    test = -np.ones((10, 20, 30))
    test[2:5, 2:5, 2:5] = np.zeros((3, 3, 3))

    # We create the value on the server. If we try to create it from different clients at once,
    # it will only take the first value it receives, and send it back to the other clients so they know which one was picked.
    test = soc.create_if_not_already_created("test", test)
    test *= 2
    comp_test0 = soc.pull_full("test")
    soc.push_as_part("test", test, [[0], [1, 4], [1, 6]], 0.5, 0.5)
    comp_test1 = soc.pull_full("test")
    print comp_test0
    print comp_test1


if __name__ == "__main__":
    main()
