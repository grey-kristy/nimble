#!/usr/bin/env python
'''Print all shared Nimble Service methods'''

import sys
import re
import argparse

def print_func(decors,func,desc, wiki=0):
    if wiki:
        f = re.sub('def ','', func)
        f = re.sub(':$','', f)
        print 'h2. %s' % f
        if desc:
            d = re.sub("'''",'', desc)
            print d
        print
    else:
        if decors: 
            print decors
        print func
        if desc:
            print desc
        print 

def read_nimble(file, wiki=0):
    try:
        f = open(file)
    except IOError as e:
        print "Can't open file '%s': %s" % (file, str(e))
        return

    all = f.readlines()
    count = 0
    for line in all:
        if '@shared' in line:
            decors = func = desc = ''
            off = 0

            # get decorators
            if '@' in all[count-2]:
                decors = '%s\n' % all[count-2].strip()
            if '@' in all[count-1] or '#' in all[count-1]:
                decors += all[count-1].strip()
        
            if '@' in all[count+1]:
                decors += all[count+1].strip()
                off = 1

            # get functions signature
            if not re.match("\s*def", all[count+1+off]):
                off += 1
            func = all[count+1+off].strip()
            if ':' not in func:
                func += all[count+2+off].strip()
                off += 1

            # get doc string
            if "'''" in all[count+2+off]:
                desc = all[count+2+off].strip()
                for i in range(30):
                    if not re.match(".*'''$", all[count+2+off+i]):
                        desc += '\n' + all[count+3+off+i].strip()
                    else:
                        break

            print_func(decors,func,desc, wiki)
        count += 1 


parser = argparse.ArgumentParser(description=
    'Parce Nimble Server class and print all shared methods')
parser.add_argument('file', help='Nimble Service file.py')
parser.add_argument('-w','--wiki', action='store_true', default=False,
    help='Output in WiKi format')

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

p = parser.parse_args()
read_nimble(p.file, p.wiki)
