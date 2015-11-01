# Copyright (c) 2014 Brad Neuman

# this is just some code to test the blame stuff

from gitBlameStats import *

repo_path = "/Users/bneuman/Documents/code/bvv4"

#run git with -C reop_path --no-pager
git_cmd = ['git', '-C', repo_path, '--no-pager']

rev = "1547f75a375a002be0d3c72aee43fa3bf0f4eb65"

limit = 10 #None

from pprint import pprint

bs = BlameStats(repo_path, debug = True)

pprint(bs.GetCommitStats(rev))
exit(0)

# for rev in bs.GetAllCommits():
#     print rev, bs.GetFilesTouchedByCommit(rev)
# exit(0)

# utility functions for dealing with multiple results
def CombineStats(lhs, rhs):
    "combine the two sets of commit stats, store into lhs"
    for filename in rhs:
        lhs[filename] = rhs[filename]

def SquashBlame(stats):
    "return a new dict from stats with a single total line number, and no entry if it would be 0"
    return stats
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

    revs = bs.GetAllCommits(limit=limit)

    total = {}

    from progressTracker import ProgressTracker
    pt = ProgressTracker(len(revs))

    for i in range(len(revs)):
        rev = revs[i]
        lastRev = None
        if i > 0:
            lastRev = revs[i-1]

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
