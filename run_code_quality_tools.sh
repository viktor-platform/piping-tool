#!/bin/bash

APP=sterke-lekdijk
echo -e "Activate virtual environment\n"
source $APP/.env/bin/activate

echo -e "Running black\n"
python3 -m black $APP/app/ $APP/tests/;
echo -e "Running isort\n"
python3 -m isort $APP/app/ $APP/tests/;
echo -e "Running mypy\n"
python3 -m mypy $APP/app --ignore-missing-imports;
echo -e "Running pylint\n"
python3 -m pylint $APP/app/ $APP/tests/ --rcfile=$APP/pyproject.toml;
echo -e "Running tests\n"
./viktor-cli test $APP

# Terminal closes on windows immediately; calling read gives user to read stdout from tools.
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    read -p "Press enter key to resume"
fi

echo -e "Deactivate virtual environment\n"
deactivate