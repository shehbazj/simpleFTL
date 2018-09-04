#!/bin/bash

# this script changes data_blocks to journal_blocks in a blockLog file

usage()
{
	echo "./getJournalBlocks.sh <cmdxxx.blockLog> <journal_block_start>"
}

if [[ "$#" -ne 2 ]]; then
	usage
	exit
fi

fname=$1
jstart=$2

while read bno ds op;
do 
	if [[ $bno -ge $jstart ]]; then
		echo "$bno journal_block $op";
	else
		echo $bno $ds $op;
	fi
done < $fname
