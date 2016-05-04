#!/opt/venvs/plumbum/bin/python3 -uIB

from logging import basicConfig, DEBUG, error, info
from pathlib import Path
from time import sleep
from traceback import print_exc

from plumbum import local, FG
from plumbum.cmd import apk, chmod, cp, curl, httpd, printf, sha256sum
from plumbum.commands.processes import ProcessExecutionError


def install_dumbinit(dumbinit_release_url: str):
    info('Installing dumb-init ... ')

    with local.cwd('/usr/local/bin/'):
        curl['--tlsv1.2', '--fail', '-LsS', '--output', 'dumb-init', dumbinit_release_url] & FG
        try:
            (printf['%s\n', 'a8defac40aaca2ca0896c7c5adbc241af60c7c3df470c1a4c469a860bd805429 *dumb-init'] | sha256sum['-c', '-s', '-'])()
        except ProcessExecutionError as error:
            raise RuntimeError('Inconsistent SHA256 hash value for dumb-init binary. ') from error
        chmod['-v', 'a+x', 'dumb-init'] & FG

    info('Installed dumb-init. ')

def configure_apache_httpd():
    info('Configuring Apache httpd ...')

    tls_conf_file_path = Path('/etc/apache2/conf.d/TLS.conf')
    temp_tls_conf_file_path = Path('/tmp') / tls_conf_file_path.relative_to('/')
    cp[temp_tls_conf_file_path, tls_conf_file_path] & FG

    ## Test validity of Apache httpd configuration.
    httpd['-t'] & FG

    info('Configured Apache httpd. ')

if __name__ == '__main__':
    try:
        basicConfig(format='%(asctime)-15s %(message)s', level=DEBUG)
        install_dumbinit(dumbinit_release_url='https://github.com/Yelp/dumb-init/releases/download/v1.0.2/dumb-init_1.0.2_amd64')
        configure_apache_httpd()
    except:
        print_exc()
        error('Exception occurred. Sleeping to help debugging inside container. ')
        sleep(100000)