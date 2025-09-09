#!/bin/bash

# Client setup
cd client
python3 -m venv client_venv
source client_venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Gateway setup
cd gateway

# Main environment
python3 -m venv main_venv
source main_venv/bin/activate
pip install -r main_requirements.txt
deactivate

# BERTScore environment
python3 -m venv bert_venv
source bert_venv/bin/activate
pip install -r bert_requirements.txt
deactivate

# BLEURT environment
python3 -m venv bleurt_venv
source bleurt_venv/bin/activate
pip install -r bleurt_requirements.txt
deactivate

# COMETKiwi22 environment
python3 -m venv cometkiwi_venv
source cometkiwi_venv/bin/activate
pip install -r cometkiwi_requirements.txt
deactivate

# Luxembedder environment
python3 -m venv luxembedder_venv
source luxembedder_venv/bin/activate
pip install -r luxembedder_requirements.txt
deactivate

cd ..