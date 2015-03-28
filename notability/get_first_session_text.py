#!/usr/bin/env python3
"""
Gets the text of a page as of the end of the first edit session.  Expects to
get a TSV of page creations.  Outputs an additional column containing the markup
or NULL if no text could be retrieved.

Usage:
    get_first_session_text -h | --help
    get_first_session_text [--api=<url>]

Options:
    -h --help    Print this documentation
    --api=<url>  The URL of the mediawiki API to hit
                 [default: https://en.wikipedia.org/w/api.php]
"""
import getpass
import sys

from docopt import docopt
from mw import api, database
from mw.lib import sessions


def main():
    args = docopt(__doc__)

    headers, creations = read_creations(sys.stdin)
    session = api.Session(args['--api'])

    session.login(input("Username: "), getpass.getpass("Password: "))

    run(creations, session, headers)

def read_creations(f):
    headers = f.readline().strip().split("\t")
    return headers, read_creations_rows(f)

def read_creations_rows(headers, f):
    for line in f:
        yield dict(zip(headers, line.strip().split("\t")))

def run(creations, session, headers):

    db = database.DB.from_params(host='analytics-store.eqiad.wmnet',
                                 user='research',
                                 read_default_file="~/.my.cnf")

    print(headers + ['eofs_rev_id', 'eofs_timestamp', 'eofs_text'])
    for creation in creations:
        rev = get_end_of_first_session(db, creation['page_id'])

        if rev is None:
            sys.stderr.write("_")
        else:
            try:
                text = get_revision_text(session, rev['rev_id'])
                encoded_text = text.replace('\n', "\\n").replace("\t", "\\t")
                print("\t".join([creation[h] for h in headers] + \
                                [str(rev['rev_id']), rev['rev_timestamp'],
                                 encoded_text]))
            except KeyError:
                sys.stderr.write("!")



def get_revision_text(session, rev_id):
    try:
        rev_doc = session.revisions.get(rev_id, properties=['content'])
    except KeyError:
        rev_doc = session.deleted_revision.get(rev_id, properties=['content'])

    return rev_doc.get('*', "")






def get_end_of_first_session(db, page_id):

    revs = db.all_revisions.query(page_id=page_id,
                                  direction="newer", limit=100)

    try:
        first_session = next(sessions.cluster(revs))
        return first_session[-1]
    except StopIteration:
        return None

if __name__ == "__main__": main()
