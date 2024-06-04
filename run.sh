#!/bin/bash
# update the project before running incase there are any important changes
git pull
poetry install

# run the project
poetry run python bot/bot.py
