#!/usr/bin/python

import argparse
from collections import defaultdict

# mainains state for each physical block
class pb:
	def __init__(self):
		self.valid_count = 0	# no of valid entries
		self.invalid_count = 0	# no of invalid entries 
		self.left = 0		# max pages - (valid + invalid)
		self.num = 0
	
	def __init__(self,num, page_per_block):
		self.num = num
		self.valid_count = 0
		self.invalid_count = 0
		self.left = page_per_block

# remove page from l2pmap, change physical block invalid and valid page count
def invalidate_page(pblist, l2pmap, lpn):
	# valid count decreases
	# invalid count increases
	# left remains the same

	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks


	pbn = l2pmap[lpn]
	block_num = pbn / page_per_block
	pblist[block_num].valid_count-=1
	pblist[block_num].invalid_count+=1
	l2pmap[lpn] = None

# allocate the next available physical page number to the logical page number
def getppn(pblist, l2pmap, lpn):
	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks

	if pblist[curr_physical_block].left is 0:
		# goto next physical block
		curr_physical_page = 0
		for i in range(0, len(pblist)):
			if pblist[i].left is not 0:
				curr_physical_block = i
				curr_physical_page = page_per_block - pblist[i].left
				break

	# allocate next physical block
	pblist[curr_physical_block].left-=1
	pblist[curr_physical_block].valid_count+=1
	assert(curr_physical_page < page_per_block)
	pbn = ((curr_physical_block * page_per_block) + curr_physical_page)
	curr_physical_page+=1
	return pbn

# map a lpn to the next available ppn using the page level mapping scheme
def page_level_map(pblist, l2pmap, lpn):
	if l2pmap[lpn] is not 0:
		print 'invalidating value'
		invalidate_page(pblist, l2pmap, lpn)
	ppn = getppn(pblist, l2pmap, lpn)
	l2pmap[lpn] = ppn
	
def block_level_map():
	return

def hybrid_map():
	return

# print l2p map and block details:
def dumpBlocks(pblist):
	for pb in pblist:
		print 'BLOCK ' + str(pb.num)
		print '======'
		print 'valid_count '+ str(pb.valid_count)
		print 'invalid_count ' +str( pb.invalid_count)
		print 'left '+ str( pb.left)
		print '======================='

def dumpMap(l2pmap):
	s = sorted(l2pmap.items())
	for k,v in s:
		print ('lbn'+str( k) + ' pbn' + str(v))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Create A FTL Simulator.\n')
	parser.add_argument('ftl_type', type=int,  help='Type 0: Page Level\n1: Block level\n2: Hybrid\n')
	parser.add_argument('dev_size', type=int,  help='Device size in MBs\n')
#	parser.add_argument('dev_size', type=int, nargs='+', help='Device size in GBs\n')
	parser.add_argument('block_size', type=int, help='Block Size in MBs\n')
	parser.add_argument('page_size', type=int, help='Page Size in KBs\n')
	parser.add_argument('trace_file', type=str, help='Input Trace File\n')
	args = parser.parse_args()

#	block from which current ppn's are being accessed
	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks
	global page_size
	global block_size
	global dev_size

	curr_physical_block = 0
	curr_physical_page = 0
	page_per_block = 0
	num_blocks = 0
	page_size = args.page_size
	block_size = args.block_size
	dev_size = args.dev_size 

	num_blocks = dev_size / block_size
	page_per_block = (args.block_size * 1024) / page_size

	l2pmap = defaultdict(int)

	pblist = []
	for i in range(1, num_blocks + 1):
		pblist.append(pb(i, page_per_block))

	lines = tuple(open(args.trace_file, 'r'))
	
	for line in lines:
		lpn=line.split(' ')[0]
		opType=line.split(' ')[1]
		
		if opType is 'READ':
			continue
		else:
			if args.ftl_type is 1:
				page_level_map(pblist, l2pmap, lpn);

			if args.ftl_type is 2:
				exit
				block_map(pblist, l2pmap, lpn);

			if args.ftl_type is 3:
				exit 
				hybrid_map(pblist, l2pmap, lpn);

	dumpBlocks(pblist)
	dumpMap(l2pmap)
