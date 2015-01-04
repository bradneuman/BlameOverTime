import blameDBQuery as query
import sqlite3

db_filename = 'blame.db'
csv_filename = 'blame.csv'

import pylab as plt

with sqlite3.connect(db_filename) as conn:
    blames = query.GetFullBlameOverTime(conn.cursor())

    authors = set([x[3] for x in blames])

    authorToIndex = {}

    num_cols = 2

    header = 'timestamp, repository, '
    for author in authors:
        authorToIndex[author] = num_cols
        num_cols += 1
        header += author + ', '

    lastCommit = None
    row = [''] * num_cols

    dates = []

    # columns: repo, timestamp, author0_lines, author1_lines, ...
    with open(csv_filename, 'w') as outfile:
        outfile.write(header + '\n')

        for line in blames:
            # print line
            ts = line[0]
            repo = line[1]
            commit = line[2]
            author = line[3]
            blameLines = line[4]

            if commit != lastCommit:
                if lastCommit:
                    # write out the old row
                    outfile.write(', '.join(row) + '\n')
                row = [''] * num_cols
                lastCommit = commit

            if row[0] == '':
                row[0] = str(ts)
                row[1] = repo
                dates.append(ts)
            idx = authorToIndex[author]
            row[idx] = str(blameLines)

        outfile.write(', '.join(row) + '\n')


    for i in range(1, len(dates)):
        if dates[i] < dates[i-1]:
            print "uh oh! %d: %d < %d" % (i, dates[i], dates[i-1])

    plt.plot(range(len(dates)), dates)
    # plt.show()
