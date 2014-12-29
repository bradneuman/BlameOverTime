# Copyright (c) 2014 Brad Neuman

# Common place to put useful re-usable queries into the blame database

def GetCurrentBlame(cursor):
    "return a list of tuples of (filename, author, num_lines) that represents"
    "the current count of lines from git blame, excluding merges"

    cursor.execute('''
    select * from 
    ( select filename,
             author,
             sum(gained_lines) - sum(lost_lines) as lines
      from blames
      group by filename,author )
    where lines > 0;
    ''')

    return cursor.fetchall()

def GetBlameOverTime(cursor):
    "return a list of tuples, in order of commits, with values (sha, author, num_lines)"

    sql = '''
    select sha, author, sum(gained_lines) - sum(lost_lines)
    from blames
    group by sha, author
    order by ROWID
    '''

    # build up the cumulative sum as we go
    ret = []
    currLines = {}

    for row in cursor.execute(sql):
        sha = row[0]
        author = row[1]
        lineDelta = row[2]

        lastLines = 0
        if author in currLines:
            lastLines = currLines[author]
        newLines = lastLines + lineDelta

        ret.append( (sha, author, newLines) )
        currLines[author] = newLines

    return ret


