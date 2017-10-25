#!/bin/bash

NUM_EVENTS=14
PIAZZA_CLASS='cpsc340'
POSTS_FILE='cpsc340_posts.txt'

# Line 10 is optional and requires that you have access to 486 W17 Piazza
# You may comment out line 10, but check that 486w17_posts.txt exists (provided in datasets.zip)
echo '[Getting posts]'
python get_posts.py $PIAZZA_CLASS $POSTS_FILE

echo '[Clustering posts by date]'
python date_cluster.py $POSTS_FILE $NUM_EVENTS

echo '[Classifying clusters]'
python classify_events.py