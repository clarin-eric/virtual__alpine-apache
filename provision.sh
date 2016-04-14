#!/bin/sh -ex

APORTS_CFG_FILE='/etc/apk/repositories'

cp "/tmp/${APORTS_CFG_FILE}" "${APORTS_CFG_FILE}"

apk --verbose --progress update --purge

apk \
  add \
  'apache2' \
  'apache2-ssl' \
  'curl' \
  'python3' \
  'tar'

mkdir -m '0755' -p '/opt/venvs/'

python3 -I \
  -B \
  -m 'venv' \
    '/opt/venvs/plumbum/'

/opt/venvs/plumbum/bin/pip \
  --disable-pip-version-check \
  --isolated \
  --no-cache-dir \
    install \
      'plumbum'
