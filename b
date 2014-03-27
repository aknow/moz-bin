#!/bin/bash

id=$1

if [ -t 0 ] ; then
  shift
  filelist=$@
else
  # pipe stdin
  filelist=$(cat)
fi

sed -i "3s/^/Bug ${id} - /g" $filelist
