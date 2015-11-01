# Copyright (c) 2015 Brad Neuman

import argparse
import blameDBQuery as query
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pprint
import sqlite3

parser = argparse.ArgumentParser(description = "Create a .csv of the blames over time from the database")
parser.add_argument('--exclude', metavar='filename',
                    help="""
                    exclude patterns specified in filename. Filename is text with one exclusion per
                    line an exclusion is a string that will be formatted in SQL as
                    'filename no like <string>'
                    e.g. lib/vendor/% or %.pdf                    
                    """,
                    default = None, nargs='?')
parser.add_argument('--map-names', metavar='filename',
                    help='''
                    read a mapping of names from 'filename'. Each line is comma seperated. The
                    first value is the "real" name of the author, and any values after that
                    will be mapped to the first value. For example, a line of:
                    Brad Neuman, bneuman, bradneuman
                    Would take any entries in the database where the author was "bneuman" or
                    "bradneuman" and would map those to "Brad Neuman"
                    ''',
                    default = None, nargs='?')
                    
                    
args = parser.parse_args()

db_filename = 'blame.db'
csv_filename = 'blame.csv'

exclusions = []
nameMap = {}

if args.exclude:
    with open(args.exclude, 'r') as infile:
        for line in infile:
            pattern = line.strip()
            if pattern != '':
                exclusions.append(pattern)

if args.map_names:
    with open(args.map_names, 'r') as infile:
        for line in infile:
            sp = line.split(',')
            if len(sp) > 1:
                realName = sp[0].strip()
                for idx in range(1,len(sp)):
                    name = sp[idx].strip()
                    nameMap[name] = realName

Y = None

with sqlite3.connect(db_filename) as conn:
    # authors = query.GetAllAuthors(conn.cursor(), nameMap)
    # print authors

    blames = query.GetFullBlameOverTime(conn.cursor(), exclusions, nameMap)

    # sort authors so they are stacked how they will be at the end
    authors2 = []
    for author in blames[-1][3]:
        authors2.append( (author, blames[-1][3][author]) )
    authors2.sort( lambda x,y : -1 if x[1] > y[1] else 1 )

    authors = [x[0] for x in authors2]

    authorPrint = list(reversed(authors))
    pprint.pprint(authorPrint)

    X = np.arange(0, len(blames), 1)

    authorToIndex = {}
    num_cols = 0
    for author in authors:
        authorToIndex[author] = num_cols
        num_cols += 1

    Y = np.zeros( (len(blames), len(authors)) )
    print Y.shape

    for rowIdx in range(len(blames)):
        line = blames[rowIdx]

        ts = line[0]
        repo = line[1]
        commit = line[2]
        authorLines = line[3]

        for author in authorLines:
            colIdx = authorToIndex[author]
            Y[rowIdx,colIdx] = authorLines[author]


P = plt.stackplot(X, Y.T)

# # make legend
# colors = [p.get_facecolor().tolist()[0] for p in P]

# patches = []
# for c, a in zip(colors, authorLines.keys()):
#     patches.append( mpatches.Patch(color = c, label = a) )

# plt.legend(handles=patches)

plt.show()
