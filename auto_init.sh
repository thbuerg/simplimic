#!/usr/bin/env bash


### INIT SCRIPT  FOR SIMPLIMIC APP DB:

# conda activate py37 
MIMIC="/nfs/research1/birney/projects/ehr/mimic/SQLite"
# 1. clear db
#touch $MIMIC/db.sqlite3_FINAL
#echo $MIMIC/db.sqlite3_FINAL
#rm $MIMIC/db.sqlite3_FINAL

# 2. clear migrations
touch simplimicapp/migrations/000xinitial
rm simplimicapp/migrations/000*initial*

# 3. run  inits
python manage.py makemigrations simplimicapp
python manage.py migrate

# populate:
python dirty_populate.py /nfs/research1/birney/projects/ehr/mimic/mimic_population

echo DONE
