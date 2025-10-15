#!/bin/bash

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
pip install git+https://github.com/lucadiliello/bleurt-pytorch.git
deactivate

# xCOMET-XL environment
python3 -m venv comet_venv
source comet_venv/bin/activate
pip install -r comet_requirements.txt
deactivate

# Luxembedder environment
python3 -m venv luxembedder_venv
source luxembedder_venv/bin/activate
pip install -r luxembedder_requirements.txt
deactivate

cd ..