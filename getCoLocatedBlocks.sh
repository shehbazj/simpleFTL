#!/bin/bash

# This script determines colocated blocks on a specific logical page number.

# Identify logical page number of the data structure of interest.
# Run workload on SFTL.
# Identify physical page number at which data structure is present in SFTL trace.
# Identify other blocks on the physical page.
# Check if any of the other pages correspond to “recovery blocks” or “previous version blocks”
# Record count.

red() {
        RED='\033[0;31m'
        NC='\033[0m'
        printf "${RED}$1 ${NC}\n"
}

blue() {
        BLUE='\033[0;34m'
        NC='\033[0m'
        printf "${BLUE}$1 ${NC}\n"
}

usage()
{
	echo ""
	echo "./getCoLocatedBlocks.sh block_size <cmdXXX> dataStructure journal_block_start"
	echo ""
	echo "block size in KBs, same as ftl.py block_size"
	echo ""
	echo "datastructure::"
	echo "  superblock"
	echo "	inode_table"
	echo "	group_descriptor"
	echo "	block_bmap"
	echo "	inode_bmap"
	echo "  directory_block"
	echo "journal block start - default for 4GB file - 491520"
	echo "need to manually inspect and see which blocks were written sequentialy in the blockLog"
	echo ""
}

check_co_located_journal_blocks()
{
	# mark any journal blocks that have the same data structure as the lpn.
	
	lpn=-1
	crash=false
	while read line;
	do
		if [[ $line = *"LPN"* ]]; then
			lpn=`echo $line | cut -d" " -f2`
			blue $lpn
		fi
		if [[ $lpn -ne -1 ]]; then
			if [[ $line = *"journal_block"* ]]; then
				red $line
				jb=`echo $line | cut -d" " -f1`
				jb=$(($jb-$jstart))
				if [[ $jb -eq 0 ]]; then
					fsblk=0
				else
					fsblk=`grep "^$jb:" $jfile | cut -d" " -f4`
				fi
				if [[ "$fsblk" =~ $re ]]; then
					blue "fsblk = $fsblk lpn = $lpn"
					if [[ "$fsblk" -eq $lpn ]]; then
						red "========== CRASH!!! ========="
						crash=true
					fi
				fi
			fi
		fi
	done < /tmp/co_located_lpns
	if [[ "$crash" = true ]]; then
		crash_count=$(($crash_count+1))
	fi

}

if [[ "$#" -lt 3 ]]; then
	usage
	exit
fi

bs=$1
blkLog=traces/$2.blockLog
out=traces/$2.bs.$bs.out
jfile=traces/$2.journal
ds=$3
jstart=${4-491520}
re='^[0-9]+$'

crash_count=0

if [[ ! -f $blkLog ]]; then
	red "FILE $blkLog \n not found in traces directory, please copy from dm-io/logs/cmdXXX/ directory"
	echo ""
	exit
fi

if [[ ! -f $out ]]; then
	red "FILE $out \n not found in traces directory, please run ./ftl.py and record its output in traces/$out file"
	exit
fi

if [[ ! -f $jfile ]]; then
	red "FILE $jfile \n not found in traces directory, please copy from dm-io/logs/cmdXXX/ directory"
	exit
fi

# 1. Identify logical page number of the data structure of interest.

cat $blkLog | grep "$ds WRITE" | cut -d" " -f1 | sort | uniq > $out.lpns

# 2. Run workload on SFTL. (already have the workload ready as cmd.out).

# 3. Identify physical page number for lpn in SFTL .out trace.
# 4. Identify other blocks on the physical page.

rm -f /tmp/co_located_lpns

while read lpn_no;
do
	ppn_no=`grep "^lpn $lpn_no " $out  | cut -d" " -f 4`
	block_no=`grep "^lpn $lpn_no " $out | cut -d" " -f 6`
	
	echo "block_no = $block_no lpn_no = $lpn_no"
	grep "block $block_no$" $out | cut -d" " -f2 | grep -v "^$lpn_no$" > $blkLog.$lpn_no.coexisting_lpns
	
	echo "LPN $lpn_no" > /tmp/co_located_lpns
	while read co_lpn_no;
	do
		grep "^$co_lpn_no " $blkLog | sort | uniq >> /tmp/co_located_lpns
	done < $blkLog.$lpn_no.coexisting_lpns
	num_co_located_lpn=`wc -l /tmp/co_located_lpns | cut -d" " -f1`
	echo "number of co_located lpns in Block $block_no = $num_co_located_lpn"
	grep "BLOCK $block_no$" -A6 $out | grep "^valid"

	check_co_located_journal_blocks
	rm $blkLog.$lpn_no.coexisting_lpns

done < $out.lpns

num_lpns=`wc -l $out.lpns | cut -d" " -f1`
red "==============================="
blue "$ds [ $crash_count / $num_lpns ]"
red "==============================="
