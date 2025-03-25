# Exempla AI API

## Prerequisites
get a .env file from the team and put it in the root of the project

### Create a virtual environment

python -m venv .venv

### Activate the virtual environment

source .venv/bin/activate <- Mac
source .venv/Scripts/activate <- Windows

### Install dependencies

pip install -r requirements.txt

### Run the app

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## Make sure you deactivate your virtual environment

run:
deactivate <- Mac / Windows
