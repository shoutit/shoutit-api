#!/usr/bin/env bash

sudo pip install --quiet flake8
flake8 ~/repo
echo "Linting python files passed"
