import csv
import os
import pickle
import sys
from collections import Counter
from itertools import combinations, product

import pandas

import re

REX_EMAIL = re.compile(
    r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?")

class Alias:
    def __init__(self,
                 uid=None,
                 login=None,
                 name=None,
                 email=None,
                 record_type=None
                 ):

        self.uid = uid
        if login is not None:
            self.login = str(login).strip()
        else:
            self.login = None
        if name is not None:
            self.name = name.strip()
        else:
            self.name = None
        self.record_type = record_type
        if email is not None:
            self.email, self.email_prefix, self.email_domain = self.parse_email(email)
        else:
            self.email = self.email_prefix = self.email_domain = None

    @staticmethod
    def parse_email(email):
        email = email.strip().lower()
        if email == 'none' or not len(email):
            email = None
        if email is not None:
            me = REX_EMAIL.search(email)
            if me is None:
                if email.endswith('.(none)'):  # FIXME why not
                    # http://stackoverflow.com/a/897611/1285620
                    email = None
        if email is not None:
            if email == '' or \
                    email.endswith('@server.fake') or \
                    email.endswith('@server.com') or \
                    email.endswith('@example.com') or \
                    email.startswith('dev@') or \
                    email.startswith('user@') or \
                    email.startswith('users@') or \
                    email.startswith('noreply@') or \
                    email.startswith('no-reply@') or \
                    email.startswith('private@') or \
                    email.startswith('announce@') or \
                    email.endswith('@email.com'):
                email = None

        prefix = None
        domain = None
        if email is not None:
            email_parts = email.split('@')
            if len(email_parts) > 1:
                prefix = email_parts[0].split('+')[0]
                if not len(prefix):
                    prefix = None
                domain = email_parts[-1]
                if not len(domain):
                    domain = None

        return email, prefix, domain

class CsvWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    writer = None

    def __init__(self, csv_file, mode='w'):
        self.f = open(csv_file, mode, newline='\n', encoding='utf-8')
        self.writer = csv.writer(self.f, delimiter=';', dialect=csv.excel)

    def writerow(self, row):
        self.writer.writerow(row)

    def writerows(self, rows):
        for row in rows:
            self.writer.writerow(row)

    def close(self):
        self.f.close()

d_alias_map = {}
clusters = {}
labels = {}


def merge(a, b, rule):
    if a in d_alias_map:
        if b in d_alias_map:
            labels[d_alias_map[a]].append(rule)
            # if both have same email and already in the alias map, check whether they are in two different clusters
            # if so, we first need to merge them
            if rule is 'EMAIL' and d_alias_map[b] < d_alias_map[a]:
                c_b = clusters.pop(d_alias_map[b])
                c_a = clusters.pop(d_alias_map[a])
                clusters[d_alias_map[b]] = sorted(c_a.union(c_b))
                # then update the alias map (we always use the smallest id as the key)
                need_update = [k for k, v in d_alias_map.items() if v == d_alias_map[a]]
                for k in need_update:
                    d_alias_map[k] = d_alias_map[b]
        else:
            d_alias_map[b] = d_alias_map[a]
            clusters[d_alias_map[a]].add(b)
            labels[d_alias_map[a]].append(rule)
    else:
        if b in d_alias_map:
            d_alias_map[a] = d_alias_map[b]
            clusters[d_alias_map[b]].add(a)
            labels[d_alias_map[b]].append(rule)
        else:
            d_alias_map[a] = a
            d_alias_map[b] = a
            clusters[a] = {a, b}
            labels[a] = [rule]


def unmask(devsMap, out_dir):
    out_dir = os.path.join(out_dir, 'idm')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'dict'), exist_ok=True)

    fakeusr_rex = re.compile(r'\A[A-Z]{8}$')

    USR_FAKE = 'FAKE'
    USR_REAL = 'REAL'

    EMAIL = 'EMAIL'
    COMP_EMAIL_PREFIX = 'COMP_EMAIL_PREFIX'
    SIMPLE_EMAIL_PREFIX = 'SIMPLE_EMAIL_PREFIX'
    PREFIX_LOGIN = 'PREFIX_LOGIN'
    PREFIX_NAME = 'PREFIX_NAME'
    LOGIN_NAME = 'LOGIN_NAME'
    FULL_NAME = 'FULL_NAME'
    SIMPLE_NAME = 'SIMPLE_NAME'
    DOMAIN = 'EMAIL_DOMAIN'
    TWO = 'TWO_OR_MORE_RULES'

    THR_MIN = 1
    THR_MAX = 10

    unmask = {}

    w_log = CsvWriter(csv_file=os.path.join(out_dir, 'idm_log.csv'))  # log delle decisioni
    writer = CsvWriter(csv_file=os.path.join(out_dir, 'idm_map.csv'))  # qui ci sono quelli ritenuti "sicuri"
    w_maybe = CsvWriter(csv_file=os.path.join(out_dir, 'idm_maybe.csv')) # qui ci sono quelli probabili, cmq inseriti nella mappa

    idx = 0
    step = 100000
    curidx = step

    aliases = {}

    # Helper structures
    d_email_uid = {}
    d_uid_email = {}

    d_prefix_uid = {}
    d_uid_prefix = {}

    d_comp_prefix_uid = {}
    d_uid_comp_prefix = {}

    d_uid_domain = {}
    d_domain_uid = {}

    d_name_uid = {}
    d_uid_name = {}

    d_login_uid = {}
    d_uid_login = {}

    all_users = devsMap

    for user in all_users:
        uid = user['id']
        login = user['login']
        name = user['name']
        email = user['email']

        if name is "github" and email is "noreply@github.com":
            continue

        unmask[uid] = uid

        if login is not None:
            m = fakeusr_rex.search(login)
            if m is not None:
                record_type = USR_FAKE
            else:
                record_type = USR_REAL
        else:
            record_type = USR_FAKE

        a = Alias(uid, login, name, email, record_type)
        aliases[uid] = a

        # - email
        d_uid_email[a.uid] = a.email
        if a.email is not None:
            d_email_uid.setdefault(a.email, {a.uid})
            d_email_uid[a.email].add(a.uid)

        # - prefix
        d_uid_prefix[a.uid] = a.email_prefix
        d_uid_comp_prefix[a.uid] = a.email_prefix
        if a.email_prefix is not None:
            if len(a.email_prefix.split('.')) > 1 or len(a.email_prefix.split('_')) > 1 or len(a.email_prefix.split('+')) > 1:  # ADDED
                d_comp_prefix_uid.setdefault(a.email_prefix, {a.uid})
                d_comp_prefix_uid[a.email_prefix].add(a.uid)
            else:
                d_prefix_uid.setdefault(a.email_prefix, {a.uid})
                d_prefix_uid[a.email_prefix].add(a.uid)

        # - domain
        d_uid_domain[a.uid] = a.email_domain
        if a.email_domain is not None:
            d_domain_uid.setdefault(a.email_domain, {a.uid})
            d_domain_uid[a.email_domain].add(a.uid)

        # - login
        d_uid_login[a.uid] = a.login
        if a.login is not None:
            d_login_uid.setdefault(a.login, {a.uid})
            d_login_uid[a.login].add(a.uid)

            if a.record_type == USR_REAL:
                d_login_uid.setdefault(a.login.lower(), {a.uid})
                d_login_uid[a.login.lower()].add(a.uid)

        # - name
        d_uid_name[a.uid] = a.name
        if a.name is not None and len(a.name):
            d_name_uid.setdefault(a.name, {a.uid})
            d_name_uid[a.name].add(a.uid)

            if len(a.name.split(' ')) == 1:
                d_name_uid.setdefault(a.name.lower(), {a.uid})
                d_name_uid[a.name.lower()].add(a.uid)

        idx += 1
        if idx >= curidx:
            print(curidx / step, '/ 30')
            curidx += step

    print('Done: helpers')

    clues = {}

    for email, set_uid in d_email_uid.items():
        if len(set_uid) > THR_MIN:
            for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(EMAIL)

    print('Done: email')

    for prefix, set_uid in d_comp_prefix_uid.items():
        if THR_MIN < len(set_uid) < THR_MAX:
            if len(prefix) >= 3:
                for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(COMP_EMAIL_PREFIX)

    print('Done: comp email prefix')

    for prefix, set_uid in d_prefix_uid.items():
        if THR_MIN < len(set_uid) < THR_MAX:
            if len(prefix) >= 3:
                for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(SIMPLE_EMAIL_PREFIX)

    print('Done: email prefix')

    for prefix in set(d_prefix_uid.keys()).intersection(set(d_login_uid.keys())):
        if len(d_prefix_uid[prefix]) < THR_MAX:
            for a, b in product(sorted(d_login_uid[prefix], key=lambda uid: int(uid)), sorted(d_prefix_uid[prefix],
                                                                                              key=lambda uid: int(
                                                                                                  uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if SIMPLE_EMAIL_PREFIX not in clues[(a, b)]:
                        clues[(a, b)].append(PREFIX_LOGIN)

    print('Done: prefix=login')

    for prefix in set(d_prefix_uid.keys()).intersection(set(d_name_uid.keys())):
        if len(d_prefix_uid[prefix]) < THR_MAX and len(d_name_uid[prefix]) < THR_MAX:
            for a, b in product(sorted(d_name_uid[prefix], key=lambda uid: int(uid)), sorted(d_prefix_uid[prefix],
                                                                                             key=lambda uid: int(uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if SIMPLE_EMAIL_PREFIX not in clues[(a, b)]:
                        clues[(a, b)].append(PREFIX_NAME)
    print('Done: prefix=name')

    for prefix in set(d_login_uid.keys()).intersection(set(d_name_uid.keys())):
        if len(d_name_uid[prefix]) < THR_MAX:
            for a, b in product(sorted(d_name_uid[prefix], key=lambda uid: int(uid)), sorted(d_login_uid[prefix],
                                                                                             key=lambda uid: int(uid))):
                if a < b:
                    clues.setdefault((a, b), [])
                    if SIMPLE_EMAIL_PREFIX not in clues[(a, b)]:
                        clues[(a, b)].append(LOGIN_NAME)
    print('Done: login=name')

    for name, set_uid in d_name_uid.items():
        if len(set_uid) > THR_MIN and len(set_uid) < THR_MAX:
            if len(name.split(' ')) > 1:
                for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(FULL_NAME)
            else:
                for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                    clues.setdefault((a, b), [])
                    clues[(a, b)].append(SIMPLE_NAME)
    print('Done: full/simple name')

    for domain, set_uid in d_domain_uid.items():
        if THR_MIN < len(set_uid) < THR_MAX:
            for a, b in combinations(sorted(set_uid, key=lambda uid: int(uid)), 2):
                clues.setdefault((a, b), [])
                clues[(a, b)].append(DOMAIN)
    print('Done: email domain')

    discarded_simple_email_prefix = list()

    for (a, b), list_clues in sorted(clues.items(), key=lambda e: (int(e[0][0]), int(e[0][1]))):
        if EMAIL in list_clues:
            merge(a, b, EMAIL)
        elif len(list_clues) >= 2:
            for clue in list_clues:
                merge(a, b, clue)
        elif FULL_NAME in list_clues:
            merge(a, b, FULL_NAME)
        elif COMP_EMAIL_PREFIX in list_clues:
            merge(a, b, COMP_EMAIL_PREFIX)
        # elif SIMPLE_EMAIL_PREFIX in list_clues: # ADDED BY PEPPONE
        #     discarded_simple_email_prefix.append((a, b))

    for uid, member_uids in clusters.items():
        members = [aliases[m] for m in member_uids]

        # Count fake/real
        c = Counter([m.record_type for m in members])
        real = [m for m in members if m.record_type == USR_REAL]
        fake = [m for m in members if m.record_type == USR_FAKE]

        # Count rules that fired
        cl = Counter(labels[uid])

        is_valid = False

        # If all have the same email there is no doubt
        if cl.get(EMAIL, 0) >= (len(members) - 1):
            is_valid = True
        # If all the REALs have the same email, assume all the FAKEs are this REAL
        elif len(Counter([m.email for m in real]).keys()) == 1:
            is_valid = True
        # If there is at most one real, at least two rules fired, and each rule applied to each pair
        elif len(real) <= 1 and len(cl.keys()) > 1 and min(cl.values()) >= (len(members) - 1):
            is_valid = True
        # At most one real, the only rule that fired is COMP_EMAIL_PREFIX or FULL_NAME
        elif len(real) <= 1 and len(cl.keys()) == 1 and \
                (cl.get(COMP_EMAIL_PREFIX, 0) or cl.get(FULL_NAME, 0)):
            is_valid = True
        # All with same full name and email domain
        elif cl.get(FULL_NAME, 0) >= (len(members) - 1) and \
                (cl.get(DOMAIN, 0) >= (len(members) - 1)):
            is_valid = True
        elif len(real) == 0 and \
                (cl.get(COMP_EMAIL_PREFIX, 0) >= (len(members) - 1) or cl.get(FULL_NAME, 0) >= (len(members) - 1)):
            is_valid = True
        else:
            # Split by email address if at least 2 share one
            if cl.get(EMAIL, 0):
                ce = [e for e, c in Counter([m.email for m in members]).items() if c > 1]
                for e in ce:
                    extra_members = [m for m in members if m.email == e]
                    extra_real = [m for m in extra_members if m.record_type == USR_REAL]
                    # extra_with_location = [m for m in extra_real if m.location is not None]

                    if len(extra_real):
                        rep = sorted(extra_real, key=lambda m: int(m.uid))[0]
                    else:
                        rep = sorted(extra_members, key=lambda m: int(m.uid))[0]

                    w_log.writerow([])
                    w_log.writerow([rep.uid, rep.login, rep.name, rep.email])
                    for a in extra_members:
                        if a.uid != rep.uid:
                            w_log.writerow([a.uid, a.login, a.name, a.email])
                            writer.writerow([a.uid, rep.uid])
                            unmask[a.uid] = rep.uid

            rep = sorted(members, key=lambda m: int(m.uid))[0]
            w_maybe.writerow([])
            w_maybe.writerow([str(cl.items())])
            for m in members:
                # Write also maybes to the alias map
                if m.uid != rep.uid:
                    unmask[m.uid] = rep.uid
                    writer.writerow([m.uid, rep.uid])
                # -- end
                w_maybe.writerow([m.uid, m.login, m.name, m.email])

        if is_valid:
            # Determine group representative
            if len(real):
                rep = sorted(real, key=lambda m: int(m.uid))[0]
            else:
                rep = sorted(members, key=lambda m: int(m.uid))[0]

            w_log.writerow([])
            w_log.writerow([str(cl.items())])
            w_log.writerow([rep.uid, rep.login, rep.name, rep.email])
            for a in members:
                if a.uid != rep.uid:
                    w_log.writerow([a.uid, a.login, a.name, a.email])
                    writer.writerow([a.uid, rep.uid])
                    unmask[a.uid] = rep.uid

    pickle.dump(unmask, open(os.path.join(out_dir, 'dict', 'alias_map.dict'), 'wb'))
    return aliases, all_users

def find_missing_aliases(aliases, _all, outputFolder):
    missing = set()
    for x in _all:
        login = x['login']
        name = x['name']
        email = x['email']
        _found = False
        for a in aliases.values():
            if login == a.email_prefix or \
                    login == a.login or \
                    name == a.name or \
                    email == a.email or \
                    email.split('@')[0].split('+')[0] == a.email_prefix:
                _found = True
                break
        if not _found:
            missing.add((login, name, email))

    with open(outputFolder + '/unmatched.txt', mode='w') as f:
        for i in missing:
            f.write(','.join(i) + '\n')
    return missing

def main(url):
    repoName = url.replace('https://github.com/', '')
    _, repo = repoName.split('/')

    sourceFolder = '../A80_Results/' + repo
    devsMapFile = os.path.join(sourceFolder, 'login_map.csv')

    devsMapData = pandas.read_csv(devsMapFile, sep=';', )
    devsMapData = devsMapData.where(pandas.notnull(devsMapData), None)

    #    devsMap = [{'id': 1, 'login': None, 'name': 'cpw', 'email': 'cpw@github.com'},
    #               {'id': 2, 'login': None, 'name': 'christian weeks', 'email': 'cpw@weeksfamily.ca'},
    #               {'id': 3, 'login': None, 'name': 'christian', 'email': 'cpw@weeksfamily.ca'},
    #               {'id': 4, 'login': None, 'name': 'christian', 'email': 'cpw+github@weeksfamily.ca'},
    #               {'id': 5, 'login': 'cpw', 'name': 'cpw', 'email': 'cpw+github@weeksfamily.ca'},
    #               {'id': 6, 'login': 'pepponefx', 'name': 'Giuseppe', 'email': 'giuiaffa@github.com'},
    #               {'id': 7, 'login': None, 'name': 'Gio', 'email': 'pepponefx@uniba.com'}]
    devsMap = []
    for i, row in devsMapData.iterrows():
        devsMap.append({'id': row['id'], 'login': row['login'], 'name': row['name'], 'email': row['email']})

    aliases, everyone = unmask(devsMap, sourceFolder)
    print('Done, looking for unmatched users')
    unmatched = find_missing_aliases(aliases, everyone, sourceFolder)
    print('Done: unmatched %s' % len(unmatched))

    ### Read Result CSV
    couplesFile = os.path.join(sourceFolder, 'idm', 'idm_map.csv')
    with open(couplesFile, 'r') as f:
        alias_couples = [rec for rec in csv.reader(f, delimiter=';')]
    #alias_couples = pandas.read_csv(couplesFile, sep=';', header=None,  names=['a', 'b'])

    ### Rebuild Chains
    chains = []
    while len(alias_couples) > 0:
        c = alias_couples.pop()
        repeat = True
        while repeat:
            repeat = False
            for el in alias_couples:
                if len(set(c).intersection(set(el))) > 0:
                    c = list(set(c).union(set(el)))
                    alias_couples.remove(el)
                    repeat = True
        chains.append(c)

    ### Assign Logins where missing
    for c in chains:
        for node in [int(n) for n in c]:
            NodeLogin = devsMapData[devsMapData['id'] == node]['login'].item()
            if NodeLogin is not None:
                devsMapData.loc[devsMapData['id'].isin(c), 'login'] = NodeLogin
                break
    print('Login Assignment Terminated!')

    ### (AGGREGATE and) Write final CSV
    resolved = devsMapData[devsMapData['login'].notnull()]
    not_resolved = devsMapData[devsMapData['login'].isnull()]

    devsMapData.to_csv(os.path.join(sourceFolder, 'unmasking_results.csv'),
                                 sep=';', na_rep='N/A', index=False, quoting=None, lineterminator='\n')
    not_resolved.to_csv(os.path.join(sourceFolder, 'unmasking_FAILED.csv'),
                       sep=';', na_rep='N/A', index=False, quoting=None, lineterminator='\n')
    resolved.to_csv(os.path.join(sourceFolder, 'unmasked_SUCCESSFUL.csv'),
                       sep=';', na_rep='N/A', index=False, quoting=None, lineterminator='\n')

if __name__ == '__main__':
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    # python script.py repoName (format: organization/repo)
    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    if len(sys.argv) < 2:
        print("Error: Not enough arguments. Please provide the list of projects file.")
        sys.exit(1)
    else:
        repoFile = sys.argv[1]
        # Reading the list of projects file and
        # iterating over the list of projects
        with open(repoFile, 'r') as f:
            for line in f:
                repoUrl = line.strip()
                main(repoUrl)
        print('Done!')
