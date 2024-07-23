#!/bin/bash
set -ex
flask db init
flask db migrate
python -m app run --host=0.0.0.0