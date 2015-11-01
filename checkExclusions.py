# Copyright (c) 2015 Brad Neuman

import blameDBQuery as query
import sqlite3
import argparse
import os

parser = argparse.ArgumentParser(description = "check for files that should maybe be excluded")
parser.add_argument('database', help="which db to check")
parser.add_argument('exclusions', help="file containing exclusions (same format at plot.py)")
parser.add_argument('-n', default=10, type=int, help='number of entries to print')
args = parser.parse_args()

if not os.path.exists(args.database):
    print "database file does not exit!"
    parser.print_help()
elif not os.path.exists(args.exclusions):
    print "exclusions file does not exit!"
    parser.print_help()
else:

    exclusions = []
    with open(args.exclusions, 'r') as infile:
        for line in infile:
            pattern = line.strip()
            if pattern != '':
                exclusions.append(pattern)

    with sqlite3.connect(args.database) as conn:
        cur = conn.cursor()

        query.PrintLargeFiles(cur, exclusions, num = args.n)
        query.PrintDiffSpikes(cur, exclusions, num = args.n)

