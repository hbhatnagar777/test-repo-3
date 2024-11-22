echo 'starting python build'

echo $PWD

python --version
pip --version
pylint --version

if [[ -z "${CI_MERGE_REQUEST_IID}" ]]; then
  FRIENDLY_BUILD="false"
else
  FRIENDLY_BUILD="true"
fi

echo $1
echo CI_PROJECT_DIR
echo $2
echo $3
echo $FRIENDLY_BUILD

python build-helper/maping.py "build" $1 $CI_PROJECT_DIR $2 $3 $FRIENDLY_BUILD
