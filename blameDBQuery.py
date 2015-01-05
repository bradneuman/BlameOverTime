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

def GetName(nameMap, name):
    "helper to return a valid name"
    nameStrip = name.strip()
    if nameStrip in nameMap:
        return nameMap[nameStrip]
    else:
        return nameStrip


def GetAllAuthors(cursor, nameMap):
    "return a list of all authors"

    names = [tpl[0] for tpl in cursor.execute('select distinct(author) from full_blames').fetchall()]

    if nameMap:
        nameSet = set()
        for name in names:
            nameSet.add( GetName(nameMap, name) )

    return list(nameSet)

def GetFullBlameOverTime(cursor, exclusions = [], nameMap = {}):
    "return the whole damn thing. TODO: dont use fetchall, write it out bit by bit"
    "list of (timestamp, repo, sha1, { author: num_lines} )"

    # go through each repository in the database, and get the blame log for each one

    # maps repository -> topo_order -> (ts, commit, { author -> num_lines} )
    repos = {}

    sql = 'select distinct(repository) from commits'
    data = cursor.execute(sql).fetchall()
    for row in data:
        repos[row[0]] = {}

    # print repos

    for repo in repos:

        sql = '''
        select commits.ts, commits.repository, commits.sha, commits.topo_order, full_blames.author, sum(lines)
        from full_blames
        inner join commits on full_blames.sha = commits.sha
        where commits.repository = (?)
        '''

        for i in range(len(exclusions)):
            sql = sql + " and full_blames.filename not like (?) "

        sql = sql + '''
        group by full_blames.sha, full_blames.author
        order by commits.topo_order
        '''

        tpl = tuple([repo] + exclusions)

        print "querying for '%s'..." % repo

        for row in cursor.execute(sql, tpl):
            ts = row[0]
            sha = row[2]
            topoOrder = row[3]
            author = GetName(nameMap, row[4])
            numLines = row[5]

            if topoOrder not in repos[repo]:
                repos[repo][topoOrder] = (ts, sha, {})
            repos[repo][topoOrder][2][author] = numLines

        # print "got %d commits from '%s'" % (len(repos[repo]), repo)


    # now merge the lists. Keep the topographic order whithin each list, but merge based on timestamp
    ret = []
    repoIdx = {}
    for repo in repos:
        repoIdx[repo] = min(repos[repo].keys())

    print "merging."

    # we want each commit entry to have a sum of the work for each author across all repositories. E.g. if the
    # commit is from repo B, we want to show the number of lines for the author as everything already done in
    # A + what was just updated in B.

    # this will keep track of the last entry for each repo, so we can add them up properly.
    # repo -> author -> num_lines
    currentWork = {}
    for repo in repos:
        currentWork[repo] = {}

    # will remove the repo when we hit the end
    while repoIdx:
        # print repoIdx

        min_times = []
        for repo in repoIdx:
            topoOrder = repoIdx[repo]
            ts = repos[repo][topoOrder][0]

            min_times.append( (ts, repo) )

        # find min timestamp
        min_entry = min(min_times, key=lambda t: t[0])
        ts = min_entry[0]
        repo = min_entry[1]

        # now we are choosing the next entry from repo
        topoOrder = repoIdx[repo]
        sha = repos[repo][topoOrder][1]
        commitWork = repos[repo][topoOrder][2]

        for author in commitWork:
            # update the currentWork for this repo
            currentWork[repo][author] = commitWork[author]

        # now create the return data by summing up the current work
        sumWork = {}
        for sumRepo in currentWork:
            for author in currentWork[sumRepo]:
                ac = 0
                if author in sumWork:
                    ac = sumWork[author]
                sumWork[author] = ac + currentWork[sumRepo][author]

        ret.append( (ts, repo, sha, sumWork) )

        # increment index, and delete it if its not there anymore
        repoIdx[repo] += 1
        if repoIdx[repo] not in repos[repo]:
            # print "finished merging %s" % repo
            del repoIdx[repo]

    return ret

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
