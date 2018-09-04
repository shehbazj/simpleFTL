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

rm -f /tmp/abc

while read bno ds op;
do 
	if [[ $bno -ge $jstart ]]; then
		echo "$bno journal_block $op" >> /tmp/abc
	else
		echo "$bno $ds $op"  >> /tmp/abc
	fi
done < $fname

mv /tmp/abc $fname
