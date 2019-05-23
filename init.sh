#!/usr/bin/env bash


### INIT SCRIPT  FOR SIMPLIMIC APP DB:

# conda activate py37 

# 1. clear db
touch db.sqlite3_RAW_v2
rm db.sqlite3_RAW_v2

# 2. clear migrations
touch simplimicapp/migrations/000xinitial
rm simplimicapp/migrations/000*initial*

# 3. run  inits
python manage.py makemigrations simplimicapp

python manage.py migrate --run-syncdb

# populate:
python dirty_populate.py $1
#python dirty_populate_FAST.py $1

echo DONE
