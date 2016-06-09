#!/usr/bin/python3

from os import environ
from pathlib import Path
from shlex import quote
from string import Template

from provisioning import provision, sh_cmd

if __name__ == '__main__':
    with provision():
        _SERVERNAME = environ['_SERVERNAME'].strip()
        assert _SERVERNAME

        WEBSITE_CFG_TEMPLATE_FILE_PATH = Path(
            '/etc/apache2/conf.d/website.conf.template')

        WEBSITE_CFG_FILE_PATH = Path('/var/www/dynamic_cfg/website.conf')
        sh_cmd('cp -a -f -- {WEBSITE_CFG_TEMPLATE_FILE_PATH:s}'
               ' {WEBSITE_CFG_FILE_PATH:s}'.format(
                   WEBSITE_CFG_TEMPLATE_FILE_PATH=quote(str(
                       WEBSITE_CFG_TEMPLATE_FILE_PATH)),
                   WEBSITE_CFG_FILE_PATH=quote(str(WEBSITE_CFG_FILE_PATH))))

        with WEBSITE_CFG_FILE_PATH.open(mode='rt+') as website_cfg_file:
            WEBSITE_CFG_TEMPLATE = Template(website_cfg_file.read())
            website_cfg_file.seek(0)
            website_cfg_file.write(WEBSITE_CFG_TEMPLATE.safe_substitute(
                _SERVERNAME=_SERVERNAME))
            website_cfg_file.truncate()
