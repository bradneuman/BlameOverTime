# Copyright (c) 2014 Brad Neuman

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires sqlite3

from gitBlameStats import *
from progressTracker import *
import argparse
import blameDBQuery as query
import os
import sqlite3
import subprocess


parser = argparse.ArgumentParser(description = "Update the blame database for the given repository")
parser.add_argument('--recursive', '-r', help='Also update all submodules',
                    default = False, action='store_true')
parser.add_argument('--dry-run', '-n', help='Dry-run (just print what would be done, don\'t do it',
                    default = False, action='store_true')
parser.add_argument('path', help="path to the repository to update")

args = parser.parse_args()

repo_paths = set([args.path])

if args.recursive:
    print 'searching for submodules...'

    def check_modules(repo):
        modfile = os.path.join(repo, '.gitmodules')
        if os.path.isfile( modfile ):
            args = ['git', '--no-pager', 'config',
                    '--file', modfile, '--get-regexp', '.*path']
            result = subprocess.check_output(args)
            for line in result.split('\n'):
                s = line.strip().split(' ')
                if len(s) == 2:
                    repo_paths.add( os.path.join( repo, s[1] ) )
                    check_modules(os.path.join( repo, s[1] ))

    check_modules(args.path)

db_filename = 'blame.db'
schema_filename = 'schema.sql'

db_is_new = not os.path.exists(db_filename)

for repo_path in repo_paths:

    path_split = os.path.split(repo_path)
    if path_split[1] == '':
        # if there is a trailing slash, the last part might be empty, so go up one
        path_split = os.path.split(path_split[0])
    repo_name = path_split[1]

    print "Run update on repository at '%s'" % repo_path

    bs = BlameStats(repo_path, debug = False)

    if db_is_new:
        print 'Creating new blank databse'
        if args.dry_run:
            continue

    with sqlite3.connect(db_filename) as conn:
        if db_is_new:
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

        print "lastest revision for '%s' is '%s'" % (repo_name, latestRev)

        revs = bs.GetAllCommits(since=latestRev)

        print 'have %d revisions to update' % len(revs)

        if not args.dry_run:

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

                # commit every now and then so we don't lose everything if something goes wrong
                if i % 20 == 0:
                    conn.commit()

            print pt.Done()
