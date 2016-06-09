#!/usr/bin/python3

from locale import getpreferredencoding
from logging import debug
from pathlib import Path
from re import fullmatch
from shlex import quote
from subprocess import PIPE

from provisioning import provision, sh_cmd


def install_management_scripts() -> None:
    sh_cmd("cp -- '/mutate_dynamic_httpd_cfg.py' '/usr/local/bin/'")
    sh_cmd("chmod 'a=rx' -- '/usr/local/bin/mutate_dynamic_httpd_cfg.py'")


def install_dumbinit(dumbinit_release_url: str) -> None:
    sh_cmd('curl --fail --location --show-error --silent --tlsv1.2 '
           "--output 'dumb-init' " + dumbinit_release_url,
           cwd='/usr/local/bin/')
    sh_cmd('printf '
           "'a8defac40aaca2ca0896c7c5adbc241af60c7c3df470c1a4c469a860bd805429 "
           "*dumb-init\n' | sha256sum -c -s '-'",
           cwd='/usr/local/bin/')
    sh_cmd("chmod 'a+x' -- 'dumb-init'", cwd='/usr/local/bin/')


def configure_apache_httpd() -> None:
    # TODO: Defect in apache2 Aport: apache system group not added.
    # Since I couldn't get gid correct afterward, directly alter OS databases.
    sh_cmd("addgroup -S 'apache'")
    sh_cmd(
        "sed -r -i 's/apache:x:100:65533:/apache:x:100:101:/' '/etc/passwd'")

    sh_cmd("mkdir -- '/var/www/dynamic_cfg/'")
    sh_cmd("touch -- '/var/www/dynamic_cfg/website.conf'")

    httpd_cfg_file_path = Path('/etc/apache2/httpd.conf')
    sh_cmd('cp -a -- {:s} {:s}'.format(
        quote(str(httpd_cfg_file_path)), quote(str(
            httpd_cfg_file_path.with_suffix('.conf.orig')))))
    with httpd_cfg_file_path.open(mode='rt+') as httpd_cfg_file:
        httpd_config_lines = httpd_cfg_file.readlines()
        httpd_cfg_file.seek(0)
        htdocs_dir_context = False
        l_act = r'\s*'
        l_any = r'[\s#]*'
        # TODO: do not use l_any but only replace active entries.
        l_dis = r'\s*#\s*'
        r_val = r'\s+[^\s#]+\n'
        # TODO: Does not handle spaces within parameters.
        r_val_1_2 = r'(?:\s+[^\s#]+){1,2}\n'
        for line in httpd_config_lines:
            if fullmatch(r'(\s*#(?:\s.*|)|)\n', line):
                continue
            elif fullmatch(
                    l_act + r'\<Directory\s+"/var/www/localhost/htdocs"\>\n',
                    line):
                htdocs_dir_context = True
                httpd_cfg_file.write(line)
            elif htdocs_dir_context and fullmatch(
                    l_act + r'AllowOverride' + r_val, line):
                httpd_cfg_file.write('AllowOverride All\n')
            elif htdocs_dir_context and fullmatch(l_act + r'\</Directory\>\n',
                                                  line):
                htdocs_dir_context = False
                httpd_cfg_file.write(line)
            elif fullmatch(l_any + r'ServerAdmin' + r_val, line):
                httpd_cfg_file.write('ServerAdmin sysops@clarin.eu\n')
            elif fullmatch(l_any + r'Group' + r_val, line):
                httpd_cfg_file.write('Group www-data\n')
            elif fullmatch(l_any + r'ServerSignature' + r_val, line):
                httpd_cfg_file.write('ServerSignature off\n')
            elif fullmatch(l_any + r'ServerTokens' + r_val, line):
                httpd_cfg_file.write('ServerTokens Prod\n')
            elif fullmatch(l_dis + r'LoadModule\s+mpm_event_module' + r_val,
                           line):
                # TODO: capture groups
                # Set MPM. WARNING: This choice of MPM is not compatible
                # with mod_php. See https://wiki.apache.org/httpd/php .
                httpd_cfg_file.write(line[1:])
            elif any(
                    fullmatch(l_act + regex, line)
                    for regex in
                (r'Listen' + r_val,
                 r'LoadModule\s+(?:mpm_prefork_module|mpm_worker_module|'
                 r'status_module)' + r_val,
                 r'(?:Access|Custom|Error|Global|Transfer)Log' + r_val_1_2)):
                httpd_cfg_file.write('#' + line)
            else:
                httpd_cfg_file.write(line)
        httpd_cfg_file.write('ErrorLog /proc/self/fd/1\n')
        httpd_cfg_file.write('GlobalLog /proc/self/fd/1 combined\n')
        httpd_cfg_file.truncate()

    sh_cmd("rm -f -- '/etc/apache2/conf.d/ssl.conf'")
    sh_cmd("cp -- '/foundation.conf' '/etc/apache2/conf.d/'")
    sh_cmd("chmod -R 'ug=rX,u+w' -- '/etc/apache2/conf.d/' "
           " '/var/www/dynamic_cfg/'")
    sh_cmd("chown -R 0:apache -- '/etc/apache2/conf.d/' "
           " '/var/www/dynamic_cfg/'")


if __name__ == '__main__':
    with provision():
        COMPLETED_PROCESS = sh_cmd(
            'apk add --upgrade '
            "'apache2=>2.4.20' 'apache2<2.4.21' "
            "'apache2-ssl=>2.4.20' 'apache2-ssl<2.4.21' "
            "'ca-certificates' "
            "'curl>=7.49.1' 'curl<7.50' "
            "'python3>=3.5.1' 'python3<3.6' 1>&2",
            stdout=PIPE)
        debug(COMPLETED_PROCESS.stderr.decode(encoding=getpreferredencoding(
            False)))

        install_management_scripts()

        install_dumbinit(
            dumbinit_release_url='https://github.com/Yelp/dumb-init/'
            'releases/download/v1.0.2/dumb-init_1.0.2_amd64')

        configure_apache_httpd()
