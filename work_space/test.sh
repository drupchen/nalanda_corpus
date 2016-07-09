#!/bin/bash
for file in /རྒྱུད།/*.txt; do
    for ((i=0; i<=30; i++)); do
        name=${file##*/}
        base=${name%.txt}
        python3  ./cutWords.py "$file" རྒྱུད།_cutwords/"${base}_segmented$i.txt"
    done
done
