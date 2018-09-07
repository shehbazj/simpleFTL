# simpleFTL

A simple flash translation layer that replays a trace containing block addresses and read/write operation.

## Input

* Block Trace
Takes in a list of block numbers and Operation Type as an input file. the format resembles

```
5188 READ
5208 READ
6164 READ
5236 READ
5276 READ
1024 WRITE
16 WRITE
16384 WRITE
```

If the Operation is not specified (READ/WRITE), then the default is write operation.

* Fail-Pairs
A list of block tuples of the format - 

```
primary\_logical\_block recovery\_logical\_block degree\_of\_loss
```

Example - for ext4, the primary block could be an inode that is written on disk. the secondary block would be the journal that is written to from which primary block is recovered in case of a failure.

## Output

* Number of Physical blocks containing both primary and recovery blocks together.

## Simulator Type

There are three types of FTL layers that can be simulated:

* Page Level FTL\
A Page level FTL maps a Logical page directly to a Physical page. If an overwrite on a logical page number occurs, the older physical page is marked invalid. A new physical page is provided to the logical page number. LtoPMap is updated to reflect updated page. BlockStat of old and new block is updated to reflect new invalid page count.
 
* Block Level FTL\
Entire logical block is mapped to a physical block. If an overwrite to a logical page number occurs, the entire block is invalidated, all entries in the older block are copied to a new block. map only contains logical to physical block mapping.

* Hybrid Level FTL\
Store LBN to PBN values, but on a an overwrite to a logical page number, the new physical block is looked up in the next free entry of the same block location. the logical to physical block number mapping is stored within each blockStat. invalidation of the entire block is done when there is no more space to write any additional blocks on the block.

## Data Structures

* LtoPMap\
A logical to physical map.
* BlockStat\
A structure containing stats for each block - block number, number of valid pages per block. occupied or free bool variable.
* next\_phy\_addr\
next physical address that can be allocated to a logical page.

## Functions

* `getNextPhysicalPage()`\
returns next valid physical page. if the LBN is already allocated, invalidate physical page, return new physical address.
* `map(lbn, pbn)`\
update lbn with pbn. assert if lbn is already mapped.
* `getFreeBlock()`\
returns a block number that has all pages invalidated.
* `getTargetBlock()`\
return block number having the least non-zero valid pages.
* `GC(X)`\
get a free block, get a target block, remap all lbns of the pbns in target block to the free block. mark victim block as available. call GC until X% of the blocks containing invalid pages have been cleaned/GC'ed.
TODO: Enhance GC to not only take free blocks but also blocks that have been filled partially.

## Garbage Collection

The code follows a _greedy_ garbage collection policy.

The garbage collection is done by default after gc\_count\% of physical blocks have been used in the file system. Garbage collection involves choosing the block containing the most number of invalid pages, selecting a destination block / free pool block, transferring valid pages from source block to the destination block. the physical pages in the source block can now be re-used during mapping.

```
Invoke GC
	Choose Victim block (blk.gc_count < curr_gc_count)
		if not found; exit
	Choose empty block (blk.gc_count < curr_gc_count)
		if not found; check for Merge Block (explained below)
	Move valid from Victim -> Empty
	Mark Empty -> Valid
	Mark Victim -> Empty
	Update GC count of both blocks to curr_gc_count.
Continue.
```

A _merge block_ is a block that is not completely empty, but has space to keep all entries of the dirty block. In case an empty block is not found, we choose a merge block, invalidate all its entires and then rewrite values back into the block, along with all entries of the _dirty block_.

## traces

* Seq\
Sequential workload
* Overwrite\
Overwrite trace used to check if previous block entries were replaced or not
* GC Trace\
A Trace that invokes GC by invalidating pages. run using ./ftl.py 1 8 512 128 traces/trace\_GC
This should create a device of 6 blocks, 8 pages and run a trace that would eventually have 11-17 blocks in block number 0.
* trace\_Merge\
A simple extension of the GC trace above that does proactive merging of available blocks.
* trace\block\_map.
see eg\_lpns/block\_map run using ./ftl.py 1 8 512 128 traces/block\_map
