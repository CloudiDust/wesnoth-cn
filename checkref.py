#!/usr/bin/env python
# coding: utf-8
# Author: Pan, Shi Zhu (poet)
# Requires: Python 2.7, Polib.
#
# This script checks all translations (.po files) to see if any items are defined
# differently in different files.
#
# Optionally, I'm also planning to automatically generate the reference book.
#
# Usage: please see wiki page at
# https://code.google.com/p/wesnoth-translation-cn/wiki/CheckRef
#

import os, polib, sys, cPickle

g_whole_words_match = False

# different OS needs different output string encoding. 
g_msgstr_encoding = 'cp936' if os.name == 'nt' else 'utf-8'

# process entry str from polib
def get_msg_str(msgstr):
    if isinstance(msgstr, list):
        return msgstr[0]
    elif isinstance(msgstr, tuple):
        return msgstr[0]
    elif isinstance(msgstr, str):
        return msgstr
    elif isinstance(msgstr, unicode):
	    # some characters can not be encoded in GBK.
        try:
            return msgstr.encode(g_msgstr_encoding)
        except:
            return "<<<Encoding Error>>>"
    else:
        print "unknown type of msgstr", type(msgstr).__name__
        return ""

class Myentry:
    def __init__(self, fname, msgid, msgstr):
        self.fname = fname
        self.msgid = msgid
        self.msgstr = get_msg_str(msgstr)
    def __eq__(self, other):
        return self.msgstr == other.msgstr
    def __ne__(self, other):
        return self.msgstr != other.msgstr

# check if an entry can be splitted into many entries. e.g. Name entry
def check_words(a_fname, entry):
    words = entry.msgid.split(",")
    lenwords = len(words)
    if lenwords == 1:
        return False
    entrystr = get_msg_str(entry.msgstr)
    transwords = entrystr.split(",")
    entrylist = []
    if lenwords == len(transwords):
        for i in range(lenwords):
            newentry = Myentry(a_fname, words[i], transwords[i])
            entrylist.append(newentry)
    else:
        transwords = entrystr.split("，")
        if lenwords == len(transwords):
            for i in range(lenwords):
                newentry = Myentry(a_fname, words[i], transwords[i])
                entrylist.append(newentry)
        else:
            #print "Possible error, translation should have %d commas: " % (lenwords)
            #print a_fname, entry.msgid, entry.msgstr
            return False
    return entrylist

# and a single translation entry
def addentry(a_podict, entry):
    if entry.msgid in a_podict:
        oldlist = a_podict[entry.msgid]
        for oldentry in oldlist:
            if oldentry == entry:
                break
        else:
            oldlist.append(entry)
    else:
        a_podict[entry.msgid] = [ entry ]

# create the database from all .po files
def mkdict(a_fname, a_podict):
    global g_whole_words_match

    po = polib.pofile(a_fname)
    for entry in po:
        if g_whole_words_match:
            newentry = Myentry(a_fname, entry.msgid, entry.msgstr)
            addentry(a_podict, newentry)
        else:
            entrylist = check_words(a_fname, entry)
            if entrylist:
                for newentry in entrylist:
                    addentry(a_podict, newentry)
            else:
                newentry = Myentry(a_fname, entry.msgid, entry.msgstr)
                addentry(a_podict, newentry)
    return a_podict

# search for all .po files in the current dir and all subdirectories
def search_files(a_files, a_dir):
    subdirs = []
    for item in os.listdir(a_dir):
        rela_path = os.path.join(a_dir,item)
        if os.path.isfile(rela_path) and not os.path.islink(rela_path):
            root, ext = os.path.splitext(rela_path)
            if ext == ".po":
                a_files.append(rela_path)
        else:
            subdirs.append(rela_path)
    for subdir in subdirs:
        a_files = search_files(a_files, subdir)
    return a_files

# check and print all duplicates, i.e. same msgid with different msgstr
def check_duplicates(podict):
    count = 0
    for entrylist in podict.itervalues():
        if len(entrylist) > 1:
            count += 1
            print "#"+str(count), '"'+entrylist[0].msgid.encode("utf-8")+'" :'
            for item in entrylist:
                print item.fname, '"'+item.msgstr+'"'
    print "Total", count, "duplicates found."

def refresh_database():
    podict = {}
    files = []
    files = search_files(files, ".")
    for fn in files:
        sys.stderr.write("\rChecking "+fn+"                                 ")
        podict = mkdict(fn, podict)
    sys.stderr.write("\rFinished checking.                                   \n")
    return podict

# command line argument check
def main():
    global g_whole_words_match

    args = " ".join(sys.argv[1:])
    if args == "-w":
        g_whole_words_match = True
    flushed = False
    if args and args != "-w":
        try:
            f = open(".checkref.cache~", "rb")
            podict = cPickle.load(f)
            f.close()
        except Exception:
            flushed = True
            podict = refresh_database()
        if args in podict:
            print "Translation found for", '"'+args+'"'
            for item in podict[args]:
                print item.fname, '"'+item.msgstr+'"'
        else:
            print "No translation found, Search substring for the first 10 matches:"
            count = 0
            for key in podict.iterkeys():
                if key.lower().find(args.lower()) >= 0:
                    for item in podict[key]:
                        count += 1
                        print "#",count,item.fname, '"'+item.msgid+'"','"'+item.msgstr+'"'
                if count >= 10:
                    break
            print "Finished search."
    else:
        if not flushed:
            flushed = True
            podict = refresh_database()
        check_duplicates(podict)

    if flushed:
        try:
            f = open(".checkref.cache~", "wb")
            cPickle.dump(podict, f, cPickle.HIGHEST_PROTOCOL)
            f.close()
        except Exception:
            # ignore error if write failed
            pass

if __name__ == "__main__":
    main()

