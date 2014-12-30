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

    revs = bs.GetAllCommits()
    print "%d total commits in '%s'" % (len(revs), repo_path)

    cur = conn.cursor()

    # get the latest revision in the database
    cur.execute('select max(ROWID), sha from blames')
    row = cur.fetchone()
    latestRev = None
    if row and row[1]:
        latestRev = row[1]
        print "'%s' is the latest rev we have in the databse" % latestRev

        try:
            idx = revs.index(latestRev)

            # revs is in reverse order, so we only need things before idx
            revs = revs[idx+1:]
        except ValueError:
            print "WARNING: latest revision '%s' not found in rev-list" % latestRev
            pass

    print 'have %d revisions to update' % len(revs)

    pt = ProgressTracker(len(revs))

    for i in range(len(revs)):
        rev = revs[i]
        print rev, pt.Update()

        lastRev = None
        if i > 0:
            lastRev = revs[i-1]

        stats = bs.GetCommitStats(rev, lastRev)

        for filename in stats:
            for author in stats[filename]:
                lines = stats[filename][author]
                val = (rev, repo_name, filename, author, lines[0], lines[1])
                # print "inserting:", val
                cur.execute('insert into blames values (?, ?, ?, ?, ?, ?)', val)
                
        
