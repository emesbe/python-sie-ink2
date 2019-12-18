#!/usr/bin/python

import argparse
import logging
import os
import sys
import io
import Sie

def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-s",
                        "--sie",
                        help="exported sie file",
                        required=True)

    args = vars(parser.parse_args())

    sie_file   = args['sie']
    ink2r_file = os.path.join('input', 'ink2r_2019.txt')

    if not os.path.exists(sie_file):
        sys.exit("Error: Non existant sie file '{}'".format(sie_file))

    if not os.path.exists(ink2r_file):
        sys.exit("Error: Non existant INK2R file '{}'".format(ink2r_file))

    sie = Sie.Sie(sie_file, ink2r_file)
    sie.Process()

if __name__ == "__main__":
    main(sys.argv[1:])
