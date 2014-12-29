import blameDBQuery as query
import sqlite3

db_filename = 'blame.db'


def showCurrBlame(conn):
    blame = query.GetCurrentBlame(conn.cursor())

    filenameLength = max(max([len(row[0]) for row in blame]), len('filename'))
    authorLength = max(max([len(row[1]) for row in blame]), len('author'))
    linesLength = 6

    format_str = "%%%ds | %%%ds | %%%ds" % (filenameLength, authorLength, linesLength)
    break_str = format_str % (filenameLength * '-', authorLength * '-', linesLength * '-')


    print format_str % ('filename', 'author', 'lines')
    print break_str

    lastFilename = None

    for line in blame:
        filename = line[0]
        if filename == lastFilename:
            print format_str % ('', line[1], line[2])
        else:
            print format_str % line

        lastFilename = filename

def blameOverTime(conn):
    blame = query.GetBlameOverTime(conn.cursor())
    import pprint
    pprint.pprint(blame)


with sqlite3.connect(db_filename) as conn:
    # showCurrBlame(conn)
    blameOverTime(conn)
