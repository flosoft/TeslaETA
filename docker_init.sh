#!/bin/bash
set -ex
flask db upgrade
python -m app run --host=0.0.0.0