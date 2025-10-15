#!/bin/bash

# Client setup
cd client
python3 -m venv client_venv
source client_venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..