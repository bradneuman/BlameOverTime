# Copyright (c) 2014 Brad Neuman

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

import os
import sqlite3
from gitBlameStats import *
from progressTracker import *
import blameDBQuery as query

repo_name = 'test'
repo_path = '/Users/bneuman/test/test-repo'

db_filename = 'blame.db'
schema_filename = 'schema.sql'

db_is_new = not os.path.exists(db_filename)

bs = BlameStats(repo_path, debug = False)

with sqlite3.connect(db_filename) as conn:
    if db_is_new:
        print 'Creating new blank databse'
        with open(schema_filename, 'rt') as f:
            schema = f.read()
        conn.executescript(schema)        

    cur = conn.cursor()

    # get the latest revision in the database
    row = query.GetLatestRevision(cur, repo_name)
    latestRev = None
    lastOrder = 0
    if row and row[0]:
        lastOrder = int(row[1])
        latestRev = row[0]

    revs = bs.GetAllCommits(since=latestRev)

    print 'have %d revisions to update' % len(revs)

    pt = ProgressTracker(len(revs))

    curr_order = lastOrder + 1

    stats = query.GetLatestFullBlames(cur, repo_name)

    for i in range(len(revs)):
        rev = revs[i]
        print rev, pt.Update()

        # first, update the commits table
        commit_ts, commit_author = bs.GetCommitProperties(rev)
        val = (rev, repo_name, curr_order, commit_ts, commit_author)
        curr_order += 1

        cur.execute('insert into commits values (?, ?, ?, ?, ?)', val)

        lastRev = None
        if i > 0:
            lastRev = revs[i-1]

        # now update the main blames table

        newStats = bs.GetCommitStats(rev)

        for filename in newStats:
            stats[filename] = newStats[filename]

        filenamesToDelete = []

        for filename in stats:
            if stats[filename]:
                for author in stats[filename]:
                    lines = stats[filename][author]
                    val = (rev, repo_name, filename, author, lines)
                    # print "inserting:", val
                    cur.execute('insert into full_blames values (?, ?, ?, ?, ?)', val)
#            else:
                # # add a row with 0 lines to show that the file is no longer present, then remove it from stats
                # val = (rev, repo_name, filename, '', 0)
                # # print "inserting:", val
                # cur.execute('insert into full_blames values (?, ?, ?, ?, ?)', val)

                # filenamesToDelete.append(filename)

        for filename in filenamesToDelete:
            del stats[filename]


                
        
