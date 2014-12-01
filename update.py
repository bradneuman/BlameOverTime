#!/usr/bin/python

# Updates (or initializes) the database and fills it in with missing commits from git. Can be insanely slow
# the first time

# Requires GitPython and sqlite3

import sqlite3
from git import *

repo_path = "."

# this database uses more memory, but is faster than the default one
repo = Repo(repo_path, odbt=GitCmdObjectDB)

# now iterate through the commits, and check which ones we don't have in the database
for commit in repo.iter_commits('master', max_count = 10):
    print commit


