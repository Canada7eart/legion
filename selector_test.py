from __future__ import print_function
import numpy as np
from param_serv.param_utils import from_axis_numbers

def selector_test():

    # we generate the test array
    arr = np.random.randint(10, size=(10, 10))
    axis_numbers = (1, 3, 5), (2, 4, 9, 6)

    # we generate a good answer in a bad way
    bad_way_LoL = [[arr[x, y] for y in axis_numbers[1]] for x in axis_numbers[0]]
    bad_way_np = np.array(bad_way_LoL)

    # we generate the values that need to be tested
    res = from_axis_numbers(arr, axis_numbers)

    # we compare
    test = res == bad_way_np

    return np.all(test)

if __name__ == "__main__":
    print(selector_test())