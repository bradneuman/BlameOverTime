# Copyright (c) 2014 Brad Neuman

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

import sqlite3

from gitBlameStats import *

repo_path = "/Users/bneuman/Documents/code/das-tools"

#run git with -C reop_path --no-pager
git_cmd = ['git', '-C', repo_path, '--no-pager']

rev = "01c2d9c463d1ffee0a1fb6a9c379aa88f76db8f3"

from pprint import pprint

bs = BlameStats(repo_path)

pprint(bs.GetCommitStats(rev))

# utility functions for dealing with multiple results
def CombineStats(lhs, rhs):
    "combine the two sets of commit stats, store into lhs"
    for filename in rhs:
        if filename not in lhs:
            lhs[filename] = []
        lhs[filename] = lhs[filename] + rhs[filename]

def SquashStats(stats):
    "combine authors with the same name, adding their lines. return new result"
    ret = {}

    for filename in stats:
        ret[filename] = []
        blameLines = {}
        for author, numLines in stats[filename]:
            nl = 0
            if author in blameLines:
                nl = blameLines[author]
            blameLines[author] = nl + numLines

        for author in blameLines:
            if blameLines[author] != 0:
                ret[filename].append( (author, blameLines[author]) )

    return ret

def blameTester():
    "simulates doing a git blame on all current files, but using the commit by commit"
    "machinery here"

    # just for testing, lets try coming up with the ending blame stats
    cmd = bs.GetGitCmd() + ['rev-list', 'HEAD', '--reverse']
    revs = subprocess.check_output(cmd).split('\n')

    total = {}

    for rev in revs:
        if len(rev) > 8: # sha-1s should be long
            print rev
            stats = bs.GetCommitStats(rev)
            CombineStats(total, stats)
            total = SquashStats(total)

    # remove empty entries (e.g. files that are deleted)
    total = {k: v for k,v in total.items() if v}

    return total

pprint(blameTester())
