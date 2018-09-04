#!/bin/bash

# This script determines colocated blocks on a specific logical page number.

# Identify logical page number of the data structure of interest.
# Run workload on SFTL.
# Identify physical page number at which data structure is present in SFTL trace.
# Identify other blocks on the physical page.
# Check if any of the other pages correspond to “recovery blocks” or “previous version blocks”
# Record count.

usage()
{
	echo "./getCoLocatedBlocks.sh <cmdXXX.blockLog> <cmdXXX.out> dataStructure"
	echo "datastructure::"
	echo "	superblock"
	echo "	inode_table"
	echo "	group_descriptor"
	echo "	block_bmap"
	echo "	inode_bmap"
}

if [[ "$#" -ne 3 ]]; then
	usage
	exit
fi

blkLog=$1
out=$2
ds=$3

# 1. Identify logical page number of the data structure of interest.

cat $blkLog | grep "$ds WRITE" | cut -d" " -f1 | sort | uniq > $out.lpns

# 2. Run workload on SFTL. (already have the workload ready as cmd.out).

# 3. Identify physical page number for lpn in SFTL .out trace.
# 4. Identify other blocks on the physical page.

while read lpn_no;
do
	ppn_no=`grep "^lpn $lpn_no " $out  | cut -d" " -f 4`
	block_no=`grep "^lpn $lpn_no " $out | cut -d" " -f 6`
	
	echo "block_no = $block_no lpn_no = $lpn_no"
	grep "block $block_no$" $out | cut -d" " -f2 | grep -v "^$lpn_no$" > $blkLog.$lpn_no.coexisting_lpns
	
	rm -f d_file
	echo "==LPN $lpn_no=="
	while read co_lpn_no;
	do
		grep "^$co_lpn_no " $blkLog | sort | uniq | tee d_file
	done < $blkLog.$lpn_no.coexisting_lpns

	num_co_located_lpn=`wc -l d_file | cut -d" " -f1`
	echo "number of co_located lpns in Block $block_no $num_co_located_lpn"
	grep "BLOCK $block_no$" -A6 $out
done < $out.lpns
