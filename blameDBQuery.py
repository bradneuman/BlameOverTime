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


def GetFullBlameOverTime(cursor):
    "return the whole damn thing. TODO: dont use fetchall, write it out bit by bit"
    "list of (timestamp, sha1, author, num_lines)"

    sql = '''
    select commits.ts, commits.repository, commits.sha, full_blames.author, sum(lines)
    from full_blames
    inner join commits on full_blames.sha = commits.sha
    group by full_blames.sha, full_blames.author
    order by commits.topo_order
    '''

    # build up the cumulative sum as we go
    ret = []
    currLines = {}

    return cursor.execute(sql).fetchall()

def GetLatestRevision(cursor, repository):
    "return a tuple of (sha, topo_order) for the latest entry in commits for the given repo"
    "return None if there are no entreis for the repo"

    sql = 'select sha, max(topo_order) from commits where repository = (?)'
    return cursor.execute(sql, (repository,)).fetchone()

def GetLatestFullBlames(cursor, repository):
    "return a dictionary of filename->author->lines from the last commit in full_blames"

    # first, select the highest topo_order commit for that repo
    row = GetLatestRevision(cursor, repository)
    if row is None or row[0] is None:
        return {}

    lastRev = row[0]

    sql = 'select filename, author, lines from full_blames where sha = (?)'

    stats = {}
    for row in cursor.execute(sql, (lastRev,)):
        filename = row[0]
        author = row[1]
        lines = row[2]
        if author == '':
            continue
        if filename not in stats:
            stats[filename] = {}
        stats[filename][author] = lines

    return stats
