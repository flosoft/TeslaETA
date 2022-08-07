#!/bin/bash
if [ -f "/data/service.db" ]; then
echo "Database file found"
python -m app run --host=0.0.0.0
else
echo "Copying empty database"
cp /service/service.db.empty /data/service.db
ls -lh /data/
python -m app run --host=0.0.0.0
fi