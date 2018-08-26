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

	maxinvalid = 0
	for block in pblist:
	#	print 'block '+str(block.num)+' iv_count = '+str(block.invalid_count) +' gc count = '+str(block.gc_count)+' curr_gc_count = '+str(curr_gc_count)
		if block.invalid_count > maxinvalid and block.gc_count < curr_gc_count:
	#		print 'got db = '+str(block.num) + ' invalid = '+str(block.invalid_count)
			db_id = block.num
			maxinvalid = block.invalid_count
	if db_id is -1:
		print 'could not find victim block to clean'
		return (-1,-1)
	else:
		print 'found dirty block '+str(db_id) + ' valid = ' + str(pblist[db_id].valid_count) + ' invalid = '+str(pblist[db_id].invalid_count)

	# empty block is any block that has left = page_per_block
	for block in pblist:
		if (block.left is page_per_block or block.valid_count is 0) and block.gc_count < curr_gc_count and block.num is not db_id:
			pblist[eb_id].invalid_count = 0
			pblist[eb_id].vald_count = 0
			pblist[eb_id].left = page_per_block
			eb_id = block.num
			break
#		else:
#			print ' not considering block ' + str(block.num) + ' left = '+str(block.left) + ' valid '+str(block.valid_count) + ' invalid_count '+str(block.invalid_count) + ' gc count ' + str(block.gc_count) + ' as a potential empty block'
	if eb_id is -1:
		# look for block that can be erased and re-written with victim block pages
		# and its own pages.
		print 'could not find empty block'
		return (eb_id, db_id)

	print 'successfully found eb_id ' +str(eb_id) + ' db_id '+str(db_id)	
	return (eb_id, db_id)

# for each ppn, scan through l2pmap and get lpn
def getlbalist(dblock, l2pmap,pblist):
	global page_per_block

	db_id = dblock.num
	lbalist = []

	if pblist[db_id].valid_count is 0:
		return lbalist
	for l,p in l2pmap.items():
#		print ' checking for ppas in the range '+str(db_id * page_per_block) + ' ' + str((db_id + 1) * page_per_block)
		if p in range(db_id * page_per_block , (db_id +1 ) * page_per_block):
			lbalist.append(l)

#	print 'lbalist size = ' + (str(len(lbalist))) + ' dblock valid count = ' + str(dblock.valid_count)
	# atleast 1 lba should be present for the dirty block
#	assert(len(lbalist) != 0)
#	print lbalist
#	print dblock.valid_count

	assert(len(lbalist) == dblock.valid_count)
	return lbalist

# on the event of not finding a completely empty block, look for any block
# whose pages can be remapped back with the dirty block pages on the same
# block

def get_merge_block(pblist, db_id, l2pmap):
	global page_per_block
	global curr_gc_count

	# get number of valid pages in dirty block
	dirty_pages = pblist[db_id].valid_count
	print 'dirty pages = '+str(dirty_pages) + ' dirty block = '+ str(db_id)
	merge_id = -1
	merge_block_lpn_list = []
	for m in pblist:
		if m.valid_count + dirty_pages <= page_per_block and m.gc_count < curr_gc_count and m.num != db_id:
			# should have been caught as an empty block!
			
#			print 'checking for merge block '+str(m.num) + ' valid count = '+ str(m.valid_count) + ' invald count = '+str(m.invalid_count) + ' left blocks = ' + str(m.left)
			#assert(m.left != page_per_block)
			merge_id = m.num
			merge_block_lpn_list = getlbalist(m,l2pmap, pblist)
			# this should have been an empty block!!
			assert(merge_block_lpn_list != [] or m.left == page_per_block)
			for lpn in merge_block_lpn_list:
				invalidate_page(pblist, l2pmap, lpn)
			assert(pblist[merge_id].valid_count == 0)
			pblist[merge_id].invalid_count = 0
			pblist[merge_id].valid_count = 0
			pblist[merge_id].left = page_per_block
			break
#		else:
#			print 'm valid count = '+ str(m.valid_count) + ' dirty pages = '+ str(dirty_pages) + ' gc count = '+ str(m.gc_count) + ' curr_gc_count = ' + str(curr_gc_count)
	return (merge_id, merge_block_lpn_list)

# 	 Choose empty block (blk.gc_count < curr_gc_count)
#                if not found; exit
#        Choose Dirty block (blk.gc_count < curr_gc_count)
#                if not found; exit
#        Move valid from Victim -> Empty
#        Mark Empty -> Valid
#        Mark Victim -> Empty
#        Update GC count of both blocks to curr_gc_count.

def gc(pblist, l2pmap):
	global gc_ratio
	global curr_gc_count
	global total_lpn_count	

	gc_ratio = 0.6
	total_pbs = len(pblist)
	full_block_count = 0
	num_gc_cycles = 0
	for block in pblist:
		if block.left is 0:
			full_block_count+=1
	if full_block_count < gc_ratio * total_pbs:
		print 'GC not required'
		return -1
	else:
		print 'performing GC'
		curr_gc_count +=1
		mb_id = -1
		m_lpn_list = []
		while True:
			(eb_id, db_id) = get_empty_and_dirty_blocks(pblist)
			if db_id is -1:
				print 'No more dirty blocks to clean for current gc cycle'
				return num_gc_cycles
						
			if eb_id is -1:
				print 'entirely empty block not found'
				print 'num lpns mapped = '+str(total_lpn_count)
				#assert(0)
				# find merge block, invalidate lbas to be remapped
				curr_gc_count+=1
				(mb_id, m_lpn_list) = get_merge_block(pblist, db_id, l2pmap)
				if mb_id is -1:
					print 'merge block also not found, returing after performing '+str(num_gc_cycles) + ' GC cycles'
					return num_gc_cycles
				else:
					print 'merge block '+ str(mb_id) + ' merge lpn '+ str(m_lpn_list)
					eb_id = mb_id
					assert(pblist[eb_id].valid_count == 0)
					pblist[eb_id].invalid_count = 0
					pblist[eb_id].left = page_per_block
				# found merge block, invalidated merge block entries
				# obtained m_lpn list - list of valid merge block ids
				# to be remapped.
			
			print 'empty block id = '+ str(eb_id)
			print 'dirty block id = '+ str(db_id)

			lpn_list = getlbalist(pblist[db_id],l2pmap, pblist)
			lpn_list.extend(m_lpn_list)
			pbpage_offset = 0
			for lpn in lpn_list:
				invalidate_page(pblist, l2pmap, lpn)
				ppn = (eb_id * page_per_block) + pbpage_offset
				l2pmap[lpn] = ppn
				pbpage_offset+=1

			# update dirty block
			pblist[db_id].valid_count = 0
			pblist[db_id].invalid_count = 0
			pblist[db_id].left = page_per_block
			pblist[db_id].gc_count = curr_gc_count
			assert(pblist[db_id].valid_count + pblist[db_id].invalid_count + pblist[db_id].left == page_per_block)

			# update empty block
			pblist[eb_id].valid_count = len(lpn_list)
			pblist[eb_id].invalid_count = 0
			pblist[eb_id].left = page_per_block - len(lpn_list)
			assert(pblist[eb_id].valid_count + pblist[eb_id].invalid_count + pblist[eb_id].left == page_per_block)
			pblist[eb_id].gc_count = curr_gc_count
			num_gc_cycles+=1

			print 'empty valid = '+str(pblist[eb_id].valid_count) + ' invalid ' + str(pblist[eb_id].invalid_count)
			print 'empty valid = '+str(pblist[db_id].valid_count) + ' invalid ' + str(pblist[db_id].invalid_count)

# remove page from l2pmap, change physical block invalid and valid page count

# this is called by two workflows:
# 1. if the lpn is being overwritten
# 2. if the gc is remapping older lpn to new physical block

def invalidate_page(pblist, l2pmap, lpn):
	# valid count decreases
	# invalid count increases
	# left remains the same

	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks

	assert(lpn in l2pmap)
	ppn = l2pmap[lpn]
	assert(ppn != -1)
	assert(ppn != None)
	block_num = ppn / page_per_block
	pblist[block_num].valid_count-=1
	pblist[block_num].invalid_count+=1
	assert(pblist[block_num].valid_count + pblist[block_num].invalid_count + pblist[block_num].left == page_per_block)
	del l2pmap[lpn]

# allocate the next available physical page number to the logical page number
def getppn(pblist, l2pmap, lpn):
	global curr_physical_block
	global curr_physical_page
	global page_per_block
	global num_blocks

	if pblist[curr_physical_block].left is 0:
#		print 'choosing new phys block for ' + str(lpn)
		ret = gc(pblist, l2pmap)
		if ret is 0:
			print 'could not perform any GC operations'
			#return -1
		# goto next physical block
		curr_physical_page = 0
		curr_physical_block = -1
		for i in range(0, len(pblist)):
			if pblist[i].left is not 0:
				curr_physical_block = i
				curr_physical_page = page_per_block - pblist[i].left
#				print 'new current block = '+ str(curr_physical_block)
				break

	if curr_physical_block is -1:
		print ' could not allocate new physical block for lpn '+str(lpn)
		return -1

	# allocate next physical block
	pblist[curr_physical_block].left-=1
	pblist[curr_physical_block].valid_count+=1
	assert(pblist[curr_physical_block].valid_count + pblist[curr_physical_block].invalid_count + pblist[curr_physical_block].left == page_per_block)
	assert(curr_physical_page < page_per_block)
	pbn = ((curr_physical_block * page_per_block) + curr_physical_page)
	curr_physical_page+=1
	return pbn

# map a lpn to the next available ppn using the page level mapping scheme

# if page already exists, invalidate the older page first.
def page_level_map(pblist, l2pmap, lpn):
	if lpn in l2pmap:
	#	print 'invalidating existing lpn=' + str(lpn) + ' ppn='+str(l2pmap[lpn])
		assert(l2pmap[lpn] != -1)
		invalidate_page(pblist, l2pmap, lpn)
	ppn = getppn(pblist, l2pmap, lpn)
	if ppn is -1:
		print 'could not map, returning'
		return -1
	assert (lpn not in l2pmap)
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
	parser.add_argument('ftl_type', type=int,  help='Type 1: Page Level\n2: Block level\n3: Hybrid\n')
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
	global total_lpn_count

	curr_physical_block = 0
	curr_physical_page = 0
	page_per_block = 0
	num_blocks = 0
	page_size = args.page_size * 1024
	block_size = args.block_size * 1024 * 1024
	dev_size = args.dev_size * 1024 * 1024
	curr_gc_count = 1
	total_lpn_count = 0

	num_blocks = dev_size / block_size
	page_per_block = block_size / page_size

	print 'page size = ' +str(page_size) + ' block size = ' +str(block_size) + ' dev size = ' +str(dev_size)

	l2pmap = defaultdict(int)

	pblist = []
	for i in range(0, num_blocks):
		pblist.append(pb(i, page_per_block))

	print 'len pblist = ' +str(len(pblist))

	lines = tuple(open(args.trace_file, 'r'))
	
	for line in lines:
		lpn=line.split(' ')[0]
		opType=line.split(' ')[1]
		
		if opType is 'READ':
			continue
		else:
			total_lpn_count +=1
			if args.ftl_type is 1:
				ret = page_level_map(pblist, l2pmap, lpn);
				if ret is -1:
					print 'cannot block map ' + str(lpn)
					print '==== CONSIDER INCREASING DEVICE SIZE ==='
					break

			if args.ftl_type is 2:
				exit(0)
				block_map(pblist, l2pmap, lpn);

			if args.ftl_type is 3:
				exit(0)
				hybrid_map(pblist, l2pmap, lpn);

	dumpBlocks(pblist)
	dumpMap(l2pmap)
