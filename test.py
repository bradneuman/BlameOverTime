# Copyright (c) 2014 Brad Neuman

# this is just some code to test the blame stuff

from gitBlameStats import *

repo_path = "/Users/bneuman/Documents/code/das-tools"
#repo_path = "/Users/bneuman/Documents/code/bvv4/lib/Anki/drive-engine/drive-basestation"

#run git with -C reop_path --no-pager
git_cmd = ['git', '-C', repo_path, '--no-pager']

rev = "d019375022b6358b64aa01e4fd849e6346beb011"

limit = 10 #None

from pprint import pprint

bs = BlameStats(repo_path, debug = False)

pprint(bs.GetCommitStats(rev))
exit(0)

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

def blameTester(limit = None):
    "simulates doing a git blame on all current files, but using the commit by commit"
    "machinery here. NOTE: this only works if there are no merges in the history"

    revs = bs.GetAllCommits(limit)

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


sb = blameTester(limit)

authorCount = {}

for filename in sb:
    for author in sb[filename]:
        ac = 0
        if author in authorCount:
            ac = authorCount[author]
        authorCount[author] = ac + sb[filename][author]

pprint(authorCount)
