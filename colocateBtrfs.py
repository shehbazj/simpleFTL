#!/usr/bin/python

# create l2pMap
# create lpn=>byteNr map
# create byteNr=>lpns defaultDict

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
	parser = argparse.ArgumentParser(description='CoLocateBTRFS.\n')
	parser.add_argument('blockLog_file', type=str)
	parser.add_argument('out_file', type=str)
	parser.add_argument('data_structure', type=str, help='interested data structure - data_block etc')
	args = parser.parse_args()

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

# create l2bmap
	lines = tuple(open(bfile, 'r'))
	l2b = {}
	for line in lines:
		if '' not in line.split(' '):
			lpn = int(line.split(' ')[0])
			byteNr = int(line.split(' ')[3])
			if byteNr == 0:
				continue
			print 'lpn = '+str(lpn) + 'byteNr = '+str(byteNr)
			assert(byteNr)
			l2b[lpn] = byteNr
#			print 'lpn = '+str(lpn) + 'l2plpn = ' +str(l2b[lpn])
#	print len(l2b)

# create b2lDict
	lines = tuple(open(bfile, 'r'))
	b2lDict = defaultdict(list)

	for line in lines:
		if '' not in line.split(' '):
			lpn = int(line.split(' ')[0])
			byteNr = int(line.split(' ')[3])
			if byteNr == 0:
				continue
			assert(byteNr)
			b2lDict[byteNr].append(lpn)

# create list of logical blocks to analyze for the data structure

	dslpn = []
	lines = tuple(open(bfile, 'r'))
	for line in lines:
		if ds in line:
			dslpn.append(int(line.split(' ')[0]))

# for each interesting lpn, check if any other lpn with same byte nr also landed on the same physical block. 
	dslpn = set(dslpn)
#	print dslpn
	for lpn in dslpn:
		uniq_crash = True
		byteNr = l2b[lpn]
		for otherLpn in b2lDict[byteNr]:
			if otherLpn == lpn:
				continue
			otherbyteNr = l2b[otherLpn]
			if byteNr == otherbyteNr:
				# check if they landed on the same physical block
				print 'lpn = '+str(lpn) + ' otherLpn = ' +str(otherLpn)
				if l2p[lpn] == l2p[otherLpn]:
					if uniq_crash is True:
						crash_count+=1
						uniq_crash = False
					print bcolors.FAIL + "CRASH" + bcolors.ENDC
					vulnerable_instances +=1
					

	# each lpn was considered twice!!
#	crash_count/=2
					
	print bcolors.WARNING + "================" +bcolors.ENDC
	print bcolors.OKBLUE + str(ds) + ' = ' + str(crash_count)+ '/' + str(len(dslpn)) + ' (' + str(vulnerable_instances) + ')' + bcolors.ENDC
	print bcolors.WARNING + "================" +bcolors.ENDC
