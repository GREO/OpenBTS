#!/bin/sh
# 
# Usage: $0 <file>
#
# Tails a file for IMSIs

tail -fn0 $1 | while read line ; do
        echo "$line" | grep \("IMSI="
        if [ $? = 0 ]
        then
                # Actions
                echo "Yeah: $line"
        fi
done
