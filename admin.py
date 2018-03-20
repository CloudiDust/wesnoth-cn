#! /bin/env python
# admin.py : script to ease some translation-related tasks.
# Copyright 2010, 2015, CloudiDust <cloudidust@gmail.com>

# See LICENSE for GNU General Public License 2.0
# That said, I don't see a reason why anyone would use this script elsewhere ;)

import sys
import os
import os.path
import shutil
import subprocess

TEXTDOMAINS = [
    'wesnoth', 'ai', 'anl', 'aoi', 'did', 'dm', 'dw', 'editor', 'ei', 'help', 'httt',
    'l', 'lib', 'low', 'manpages', 'manual', 'multiplayer', 'nr', 'sof', 'sota',
    'sotbe', 'tb', 'test', 'thot', 'trow', 'tsg', 'tutorial', 'units', 'utbs'
]

ROOTS = {'in': 'translations', 'out': 'target', 'dist': 'target/dist', 'official': '../wesnoth'}

def po_path(textdomain, root='in'):
    return '%s/wesnoth/po/%s/zh_CN.po' % (ROOTS[root], textdomain)

def pot_path(textdomain):
    return '%s/po/%s/%s.pot' % (ROOTS['official'], textdomain, textdomain)

def mo_path(textdomain):
    return ('%s/mo/wesnoth/translations/zh_CN/LC_MESSAGES/%s.mo' %
        (ROOTS['out'], textdomain))

def pot_remote_url(textdomain):
    return ('http://svn.gna.org/svn/wesnoth/trunk/po/%s/%s.pot' %
        (textdomain, textdomain))

def ensure_dir_exists_or_inform(path):
    path = os.path.abspath(path)
    if os.path.isdir(path):
        return True
    elif os.path.isfile(path):
        print 'Warning: directory expected, regular file found: %s' % path
        return False
    else:
        try:
            os.makedirs(path)
            return True
        except OSError:
            print 'Warning: cannot create directory: %s' % path
            return False
        
def ensure_parent_exists_or_inform(path):
    parent = os.path.dirname(path)
    return ensure_dir_exists_or_inform(parent)

# Merge the po file of the specified textdomain with its pot file.
# Source location references are omitted as they provide little value over
# the already helpful auto comments. Useless huge diffs that only record
# source location changes are also avoided.
def merge(textdomain):
    po = po_path(textdomain)
    pot = pot_path(textdomain)

    if not os.path.isfile(po):
        print 'Warning: skipped textdomain %s, no catalog file.' % textdomain
    elif not os.path.isfile(pot):
        print 'Warning: skipped textdomain %s, no template file.' % textdomain
    else:
        print 'Merging ' + textdomain + '...'
        cmd = ['msgmerge', '--quiet', '--no-location', '--update', po, pot]
        sys.stdout.flush()
        subprocess.call(cmd)

def merge_cmd(textdomains):
    for textdomain in textdomains:
        merge(textdomain)

# Normalize the po file of the specified textdomain to the standard layout.
def normalize(textdomain):
    po = po_path(textdomain)
    if not os.path.isfile(po):
        print 'Warning: skipped textdomain %s, no catalog file.' % textdomain
    else:
        print 'Normalizing ' + textdomain + '...'
        cmd = ['msgattrib', po, '-o', po, '--no-obsolete']
        sys.stdout.flush()
        subprocess.call(cmd)

def normalize_cmd(textdomains):
    for textdomain in textdomains:
        normalize(textdomain)

# Compile the po file of the specified textdomain into a well-placed mo file.
def compile(textdomain):
    po = po_path(textdomain)
    mo = mo_path(textdomain)

    if not os.path.isfile(po):
        print 'Warning: skipped textdomain %s, no catalog file.' % textdomain
    elif not ensure_parent_exists_or_inform(mo):
        print 'Warning: skipped textdomain %s.'
    else:
        print 'Compiling ' + textdomain + '...'
        cmd = ['msgfmt',  po, '-o', mo]
        sys.stdout.flush()
        subprocess.call(cmd)

def compile_cmd(textdomains):
    for textdomain in textdomains:
        compile(textdomain)

# Make a distribution package for submission.
# The po files in the official repo have source location references,
# so as not to create huge diffs there, we do some preparation.
def prepare_for_dist(textdomain):
    pot = pot_path(textdomain)
    po = po_path(textdomain)
    dist_po = po_path(textdomain, 'dist')

    if not os.path.isfile(pot):
        print 'Warning: skipped textdomain %s, no template file.' % textdomain
        return None
    elif not os.path.isfile(po):
        print 'Warning: skipped textdomain %s, no catalog file.' % textdomain
        return None
    elif not ensure_parent_exists_or_inform(dist_po):
        print 'Warning: skipped textdomain %s.'
        return None
    
    print 'Preparing ' + textdomain + '...'
    sys.stdout.flush()
    shutil.copy(po, dist_po)
    merge_cmd = ['msgmerge', '-qo', dist_po, dist_po, pot]
    subprocess.call(merge_cmd)
    return os.path.relpath(dist_po, ROOTS['dist']).replace('\\', '/')
    
def dist_cmd(textdomains):
    dist_pos = [prepare_for_dist(textdomain) for textdomain in textdomains]
    dist_pos = [path for path in dist_pos if path is not None]
    print 'Creating distribution...'
    tar_cmd = ['tar', 'cJ', '-f', ROOTS['dist'] + '/wesnoth_cn.tar.xz', '-C', ROOTS['dist']]
    tar_cmd.extend(dist_pos)
    sys.stdout.flush()
    subprocess.call(tar_cmd)

def usage_and_exit():
    print 'Usage: admin.py merge|normalize|compile|dist [textdomain ...]'
    sys.exit(1)

COMMANDS = {
    'merge': merge_cmd,
    'normalize': normalize_cmd,
    'compile': compile_cmd,
    'dist': dist_cmd
}

def parse_args_and_fill_default():
    if len(sys.argv) == 1:
        return (None, [])
    cmd = COMMANDS.get(sys.argv[1])
    if cmd is None:
        return (None, [])
    tds = sys.argv[2:]
    if len(tds) == 0:
        tds = TEXTDOMAINS
    return (cmd, tds)

# Textdomain names specified in the command line can be abbreviated, i.e.,
# the prefix 'wesnoth-' can be omitted, so normalization is needed.
def normalize_textdomain(textdomain):
    if textdomain.startswith('wesnoth'):
        normalized = textdomain
    else:
        normalized = 'wesnoth-' + textdomain
    return normalized

def normalize_textdomains(textdomains):
    return [normalize_textdomain(textdomain) for textdomain in textdomains]

def split_textdomains(textdomains):
    known = []
    unknown = []
    for textdomain in textdomains:
        if textdomain in TEXTDOMAINS:
            known.append(textdomain)
        else:
            unknown.append(textdomain)
    return (known, unknown)

def warn_about_unknown(unknown):
    if len(unknown) == 0: return
    print 'Warning: skipped unknown textdomain: ' + ','.join(unknown)

def main():
    global TEXTDOMAINS
    command, textdomains = parse_args_and_fill_default()
    if command is None:
        usage_and_exit()

    TEXTDOMAINS = normalize_textdomains(TEXTDOMAINS)
    textdomains = normalize_textdomains(textdomains)
    known, unknown = split_textdomains(textdomains)
    warn_about_unknown(unknown)

    command(known)

    print 'Done.'

if __name__ == "__main__":
    main()
