#!/usr/bin/env bash


### INIT SCRIPT  FOR SIMPLIMIC APP DB:

# conda activate py37 

# 1. clear db
touch db.sqlite3
rm db.sqlite3

# 2. clear migrations
touch simplimicapp/migrations/000xinitial
rm simplimicapp/migrations/000*initial*

# 3. run  inits
python manage.py makemigrations simplimicapp

python manage.py migrate --run-syncdb

echo DONE
