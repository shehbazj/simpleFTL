#!/usr/bin/python

import argparse
from collections import defaultdict

# pb - physical block
# ppn - physical page number. block contains multiple pages
# page_per_block - number of physical pages in 1 block.
# lpn - logical page number - the logical page number in the trace.

# mainains state for each physical block
class pb:
	def __init__(self):
		self.valid_count = 0	# no of valid page entries
		self.invalid_count = 0	# no of invalid page entries 
		self.left = 0		# no of pages left = total pages - (valid_count + invalid_count)
		self.num = 0		# block number
		self.gc_count = 0	# gc id. each block should have either same
					# gc id or a gc id less than curr_gc_id
	
	def __init__(self,num, page_per_block):
		self.num = num		
		self.valid_count = 0
		self.invalid_count = 0
		self.left = page_per_block
		self.gc_count = 0

def get_empty_and_dirty_blocks(pblist):
	global curr_gc_count

	eb_id = -1
	db_id = -1
	# empty block is any block that has left = page_per_block
	for block in pblist:
		if block.left is page_per_block and block.gc_count < curr_gc_count:
			eb_id = block.num
			break
	if eb_id is -1:
		print 'could not find empty block, exiting'
		return (-1,-1)
	
	maxinvalid = 0
	for block in pblist:	
		if block.invalid_count > maxinvalid and block.gc_count < curr_gc_count:  
			db_id = block.num
			maxinvalid = block.invalid_count
	if db_id is -1:
		print 'could not find victim block to clean'
		return (-1,-1)

	return (eb_id, db_id)

# for each ppn, scan through l2pmap and get lpn
def getlbalist(dblock, l2pmap):
	global page_per_block

	db_id = dblock.num
	lbalist = []
	for ppn in range(db_id * page_per_block , db_id * page_per_block + page_per_block):
		for l,p in l2pmap.items():
			if p is ppn:
				print 'looking for ppn ' + str(ppn) + ' got lbn ' + l
				lbalist.append(l)
	print 'lbalist size = ' + (str(len(lbalist))) + ' dblock valid count = ' + str(dblock.valid_count)
	print lbalist
	assert(len(lbalist) == dblock.valid_count)
	return lbalist

# 	 Choose empty block (blk.gc_count < curr_gc_count)
#                if not found; exit
#        Choose Dirty block (blk.gc_count < curr_gc_count)
#                if not found; exit
#        Move valid from Victim -> Empty
#        Mark Empty -> Valid
#        Mark Victim -> Empty
#        Update GC count of both blocks to curr_gc_count.

def gc(pblist):

	global gc_ratio
	global curr_gc_count
	gc_ratio = 0.6
	total_pbs = len(pblist)
	full_block_count = 0
	for block in pblist:
		if block.left is 0:
			full_block_count+=1
	if full_block_count < gc_ratio * total_pbs:
		print 'GC not required'
		return 0
	else:
		print 'performing GC'
		curr_gc_count +=1
		while True:
			(eb_id, db_id) = get_empty_and_dirty_blocks(pblist)
			if eb_id is -1 or db_id is -1:
				print 'ENOSPC no empty and/or dirty blocks to clean!!!'
				return 0
			
			print 'empty block id = '+ str(eb_id)
			print 'dirty block id = '+ str(db_id)
			
			lpn_list = getlbalist(pblist[db_id],l2pmap)
			pbpage_offset = 0
			for _lpn in lpn_list:
				l2pmap[_lpn] = (eb_id * page_per_block) + pbpage_offset

			# update empty block
			pblist[db_id].valid_count = 0
			pblist[db_id].invalid_count = 0
			pblist[db_id].left = page_per_block
			pblist[db_id].gc_count = curr_gc_count

			# update victim block
			pblist[eb_id].valid_count = len(lpn_list)
			pblist[eb_id].invalid_count = 0
			pblist[eb_id].left = page_per_block - len(lpn_list)
			pblist[eb_id].gc_count = curr_gc_count


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
	l2pmap[lpn] = -1

# allocate the next available physical page number to the logical page number
def getppn(pblist, l2pmap, lpn):
	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks

	if pblist[curr_physical_block].left is 0:
		print 'choosing new phys block for ' + str(lpn)
		ret = gc(pblist)
		if ret is -1:
			print 'could not map lpn'
			return -1
		# goto next physical block
		curr_physical_page = 0
		for i in range(0, len(pblist)):
			if pblist[i].left is not 0:
				curr_physical_block = i
				curr_physical_page = page_per_block - pblist[i].left
				print 'new current block = '+ str(curr_physical_block)
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
#	if l2pmap[lpn] is not 0 and l2pmap[lpn] is not None:
	print 'logical page ' + str(lpn)
	if l2pmap[lpn] is not -1:
#		print 'invalidating existing lpn=' + lpn + ' ppn='+str(l2pmap[lpn])
		invalidate_page(pblist, l2pmap, lpn)
	ppn = getppn(pblist, l2pmap, lpn)
	if ppn is -1:
		print 'could not map, returning'
		return -1
	l2pmap[lpn] = ppn
	return 0
	
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
		print 'gc_count' + str(pb.gc_count)
		print '======================='

def dumpMap(l2pmap):
	s = sorted(l2pmap.items())
	for k,v in s:
		print ('lpn'+str( k) + ' ppn' + str(v))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Create A FTL Simulator.\n')
	parser.add_argument('ftl_type', type=int,  help='Type 0: Page Level\n1: Block level\n2: Hybrid\n')
	parser.add_argument('dev_size', type=int,  help='Device size in MBs\n')
	parser.add_argument('block_size', type=int, help='Block Size in MBs\n')
	parser.add_argument('page_size', type=int, help='Page Size in KBs\n')
	parser.add_argument('trace_file', type=str, help='Input Trace File\n')
	args = parser.parse_args()

#	block from which current ppn's are being accessed
	global curr_gc_count
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
	curr_gc_count = 1

	num_blocks = dev_size / block_size
	page_per_block = (args.block_size * 1024) / page_size

	l2pmap = defaultdict(lambda: -1)

	pblist = []
	for i in range(0, num_blocks):
		pblist.append(pb(i, page_per_block))

	lines = tuple(open(args.trace_file, 'r'))
	
	for line in lines:
		lpn=line.split(' ')[0]
		opType=line.split(' ')[1]
		
		if opType is 'READ':
			continue
		else:
			if args.ftl_type is 1:
				ret = page_level_map(pblist, l2pmap, lpn);
				if ret is -1:
					print 'cannot block map ' + str(lpn)
					break

			if args.ftl_type is 2:
				exit(0)
				block_map(pblist, l2pmap, lpn);

			if args.ftl_type is 3:
				exit(0)
				hybrid_map(pblist, l2pmap, lpn);

	dumpBlocks(pblist)
	dumpMap(l2pmap)
