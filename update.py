#!/usr/bin/python

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

import sqlite3
import subprocess

repo_path = "/Users/bneuman/Documents/code/das-tools"
#run git with -C reop_path --no-pager

git_cmd = ['git', '-C', repo_path, '--no-pager']

rev = "1a072335170fb8c8008b7ee1c991faaeaaaf955a"


def GetDiffStats(rev, debug = False):
    "return a tuple of 4 things:\n"
    "  * a dictionary of old filename -> list of tuple (lineNum, numberOfLines). These are the lines\n"
    "    in the old file that were deleted by this commit\n"
    "  * a dictionary of new filename -> number of lines added by the author\n"
    "  * a dictionary of new filename -> number of lines removed by the author (will be negative)\n"
    "  * a list of tuples of file renames (oldFilename, newFilename)"

    def dprint(s):
        if debug:
            print("    # %s\n" % s)


    cmd = git_cmd + ['diff',
                     '-C', # find copies
                     '-M', # find moves
                     '-U0', # don't print extra lines around diff
                     '--no-color',
                     rev+'^', # diff between rev and what came before rev
                     rev
                 ]

    oldLinesPerFile = {}
    numNewLinesPerFile = {} # key is new file
    numDeletedLinesPerFile = {} # key is new file
    renames = []

    oldFile = ''
    newFile = ''

    data = subprocess.check_output(cmd)
    for line in data.split('\n'):
        if debug:
            print line
        if len(line)>0:
            if line[:4] == "diff":
                oldFile = None
                newFile = None
            elif line[:3] == '---':
                if line[:14] != "--- /dev/null":
                    oldFile = line[6:]
                    dprint(" old file is %s" % oldFile)
            elif line[:3] == '+++':
                newFile = line[6:]
                dprint(" new file is %s" % newFile)
                # this comes second
                if oldFile and oldFile != newFile:
                    renames.append( (oldFile, newFile) )
                
            elif line[:2] == '@@':
                # find ending @@
                endIdx = line.find('@@', 3)
                if endIdx > 2:
                    for lineChunk in line[3:endIdx-1].split(' '):
                        commaIdx = lineChunk.find(',')
                        if commaIdx >= 0:
                            try:
                                newLineInfo = (int(lineChunk[1:commaIdx]), int(lineChunk[commaIdx+1:]))
                            except ValueError:
                                dprint(" value error! couldn't parse!")
                                break # for lineChunk
                        else:
                            try:
                                # if there's one line, no comma is printed
                                newLineInfo = (int(lineChunk[1:]), 1)
                            except ValueError:
                                dprint(" value error! couldn't parse!")
                                break # for lineChunk


                        if newLineInfo[1] > 0:
                            if lineChunk[0] == '-':
                                if oldFile not in oldLinesPerFile:
                                    oldLinesPerFile[oldFile] = []
                                oldLinesPerFile[oldFile].append(newLineInfo)
                                dprint("oldLines")

            # these are at the bottom ebecause they could fuck up with '---' or '+++'
            elif line[0] == '+':
                dprint("line added")
                nc = 0
                if newFile in numNewLinesPerFile:
                    nc = numNewLinesPerFile[newFile]
                numNewLinesPerFile[newFile] = nc + 1
            elif line[0] == '-':
                dprint("line removed")
                dc = 0
                if newFile in numDeletedLinesPerFile:
                    dc = numDeletedLinesPerFile[newFile]
                numDeletedLinesPerFile[newFile] = dc - 1

    return (oldLinesPerFile, numNewLinesPerFile, numDeletedLinesPerFile, renames)


oldLinesPerFile, numNewLinesPerFile, numDeletedLinesPerFile, renames = GetDiffStats(rev)

from pprint import pprint

pprint(oldLinesPerFile)
pprint(numNewLinesPerFile)
pprint(numDeletedLinesPerFile)
pprint(renames)
