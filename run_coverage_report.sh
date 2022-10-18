pip install coverage -q;

if [ $# -gt 0 ]
then
  coverage run --rcfile=./.coveragerc -m unittest discover -s tests/"$@";
else
  coverage run --rcfile=./.coveragerc -m unittest discover -s tests;
fi
coverage report --skip-covered || true