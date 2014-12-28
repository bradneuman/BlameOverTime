# Copyright (c) 2014 Brad Neuman

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

import sqlite3

from gitBlameStats import *

repo_path = "/Users/bneuman/Documents/code/das-tools"

#run git with -C reop_path --no-pager
git_cmd = ['git', '-C', repo_path, '--no-pager']

rev = "517430b32693cd138b5b39461d951560850bc9be"

from pprint import pprint

bs = BlameStats(repo_path, debug = False)

# pprint(bs.GetCommitStats(rev))

# utility functions for dealing with multiple results
def CombineStats(lhs, rhs):
    "combine the two sets of commit stats, store into lhs"
    for filename in rhs:
        if filename not in lhs:
            lhs[filename] = {}
        for author in rhs[filename]:
            lTuple = (0, 0)
            if author in lhs[filename]:
                lTuple = lhs[filename][author]
            lhs[filename][author] = tuple( map(sum, zip(lTuple, rhs[filename][author])) )

def SquashBlame(stats):
    "return a new dict from stats with a single total line number, and no entry if it would be 0"
    ret = {}
    for filename in stats:
        for author in stats[filename]:
            tpl = stats[filename][author]
            if tpl[0] != tpl[1]:
                # add it
                if filename not in ret:
                    ret[filename] = {}
                ret[filename][author] = tpl[0] - tpl[1]

    return ret

def blameTester():
    "simulates doing a git blame on all current files, but using the commit by commit"
    "machinery here"

    # just for testing, lets try coming up with the ending blame stats
    cmd = bs.GetGitCmd() + ['rev-list', 'HEAD', '--reverse']
    revs = subprocess.check_output(cmd).split('\n')

    total = {}

    from progressTracker import ProgressTracker
    pt = ProgressTracker(len(revs))

    for rev in revs:
        pt.Update()
        if len(rev) > 8: # sha-1s should be long
            print rev, pt
            stats = bs.GetCommitStats(rev)
            CombineStats(total, stats)

    # remove empty entries (i.e. changes that net to 0)
    return SquashBlame(total)

pprint(blameTester())
