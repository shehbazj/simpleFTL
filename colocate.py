#!/usr/bin/python

# get journal size, wc -l *.journal
# check if journal was overwritten - last line of *.journal is not Unknown

# read lpn2pbn map in memory.

# read blockLog file, extract all block numbers of the journal (lets call them journalBlockNumber), create journal_blk_to_phys_map of 0,1,2... -> l2pmap[journalBlockNumber].
# read *.journal,  for each entry, generate a defaultdict with FS number at index idx (extracted from FS field in journal) and journal_blk_to_phys_map[idx].

# FS page to list of blocks where journal entries are placed for fs blk

# for each "interesting" block (data, superblock, inode_table) in l2p map:
#	primary block location = l2p[interesting block]
#	if primary block location in FSpageList[primary block]
#		crash!

import argparse
import os
from collections import defaultdict

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='CoLocate.\n')
	parser.add_argument('journal_file', type=str)
	parser.add_argument('blockLog_file', type=str)
	parser.add_argument('out_file', type=str)
	parser.add_argument('data_structure', type=str, help='interested data structure - data_block etc')
	args = parser.parse_args()

	jfile = args.journal_file
	bfile = args.blockLog_file
	ofile = args.out_file
	ds = args.data_structure

	crash_count = 0
	vulnerable_instances = 0

	print 'initializing l2p map'

	l2p = {}

# load l2pmap

	lines = tuple(open(ofile, 'r'))
	for line in lines:
		if 'lpn' in line and 'block' in line: 
			l2p[int(line.split(' ')[1])] = int(line.split(' ')[5].rstrip())

# journal to physical block number mapping

	print 'initializing journal to physical map'

	jpn = []
	lines = tuple(open(bfile, 'r'))
	
	for line in lines:
		if 'journal_block' in line and 'WRITE' in line:
			if int (line.split(' ')[0]) in l2p:
				jpn.append(int(l2p[int(line.split(' ')[0])]))

#	print jpn

# create FS journal block list

	print 'creating lpn - journal physical block list'

	fs_jpnlist = defaultdict(list)
	lines = tuple(open(jfile, 'r'))

	for line in lines:
		if 'FS Block' in line and 'Unknown' not in line:
			fsblk = int(line.split('FS Block ')[1].rstrip())
			jindex = int(line.split(':')[0])
			fs_jpnlist[fsblk].append( jpn[jindex])
				
		if 'Superblock' in line:
			fsblk = 491520
			jindex = int(line.split(':')[0])
			fs_jpnlist[fsblk].append( jpn[jindex])

#	print 'fs_jpnlist'
#	print fs_jpnlist

# get block numbers of interesting data structures	

	print 'extracting important data structure block numbers'

	plist = []
	lines = tuple(open(bfile, 'r'))

	for line in lines:
		if ds in line and 'WRITE' in line:
			plist.append(int(line.split(' ')[0]))


	for page in plist:
		primary_block_location = l2p[int(page)]
		print 'page'
		print page
		print 'fs_jpnlist'
		uniq_crash = True
		for v in fs_jpnlist.values():
			if primary_block_location in v:
				if uniq_crash:
					crash_count+=1
					uniq_crash = False
				print bcolors.FAIL + ' CRASH' + bcolors.ENDC
				vulnerable_instances+=1
					
	print bcolors.WARNING + "================" +bcolors.ENDC
	print bcolors.OKBLUE + str(ds) + ' = ' + str(crash_count)+ '/' + str(len(plist)) + ' (' + str(vulnerable_instances) + ')' + bcolors.ENDC
	print bcolors.WARNING + "================" +bcolors.ENDC
