#!/usr/bin/env python2
from __future__ import print_function, with_statement, division, generators
import sys, argparse

from param_serv.param_utils import *
import socialism.Client

def main():
    soc = socialism.Client()
    soc.pull_full_param("test")
    soc.push_param_from_axis_numbers("test", (3, 2, 1), (3, 2, 1))
    soc.pull_full_param("test")
    print(soc.db["test"])

if __name__ == "__main__":
    main()