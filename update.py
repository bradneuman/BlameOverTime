# Copyright (c) 2014 Brad Neuman

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

import os
import sqlite3
from gitBlameStats import *
from progressTracker import *

repo_name = 'das-tools'
repo_path = '/Users/bneuman/Documents/code/das-tools'

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
    cur.execute('select max(topo_order), sha from commits')
    row = cur.fetchone()
    latestRev = None
    lastOrder = 0
    if row and row[1]:
        lastOrder = int(row[0])
        latestRev = row[1]

    revs = bs.GetAllCommits(since=latestRev)

    print 'have %d revisions to update' % len(revs)

    pt = ProgressTracker(len(revs))

    curr_order = lastOrder

    for i in range(len(revs)):
        rev = revs[i]
        print rev, pt.Update()

        # first, update the commits table
        commit_ts, commit_author = bs.GetCommitProperties(rev)
        val = (rev, curr_order, commit_ts, commit_author)
        curr_order += 1

        cur.execute('insert into commits values (?, ?, ?, ?)', val)

        lastRev = None
        if i > 0:
            lastRev = revs[i-1]

        # now update the main blames table

        stats = bs.GetCommitStats(rev, lastRev)

        for filename in stats:
            for author in stats[filename]:
                lines = stats[filename][author]
                val = (rev, repo_name, filename, author, lines[0], lines[1])
                # print "inserting:", val
                cur.execute('insert into blames values (?, ?, ?, ?, ?, ?)', val)
                
        
