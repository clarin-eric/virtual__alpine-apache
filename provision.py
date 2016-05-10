#!/opt/venvs/plumbum/bin/python3 -uIB

from logging import basicConfig, DEBUG, error, info
from pathlib import Path
from time import sleep
from traceback import print_exc

from plumbum import local, FG
from plumbum.cmd import apk, chmod, cp, curl, httpd, ln, mkdir, printf, rm, sed, sha256sum, tee
from plumbum.commands.processes import ProcessExecutionError


def install_dumbinit(dumbinit_release_url: str):
    info('Installing dumb-init ... ')

    with local.cwd('/usr/local/bin/'):
        curl['--fail', '--location', '--show-error', '--silent', '--tlsv1.2', '--output', 'dumb-init', dumbinit_release_url] & FG
        try:
            (printf['%s\n', 'a8defac40aaca2ca0896c7c5adbc241af60c7c3df470c1a4c469a860bd805429 *dumb-init'] | sha256sum['-c', '-s', '-'])()
        except ProcessExecutionError as error:
            raise RuntimeError('Inconsistent SHA256 hash value for dumb-init binary. ') from error
        chmod['a+x', 'dumb-init'] & FG

    info('Installed dumb-init. ')

def configure_apache_httpd():
    info('Configuring Apache httpd ...')

    tls_conf_file_path = Path('/etc/apache2/conf.d/TLS.conf')
    temp_tls_conf_file_path = Path('/tmp') / tls_conf_file_path.relative_to('/')
    cp[temp_tls_conf_file_path, tls_conf_file_path] & FG

    rm['-f', '/etc/apache2/conf.d/ssl.conf'] & FG

    mkdir['-m', 'a=rx,u+w', '/run/apache2/'] & FG
    ## TODO:
    # mkdir['-m', 'a=,u=rwx', '/var/cache/apache2/'] & FG
    # chown['apache:apache', '/var/cache/apache2/'] & FG

    sed['-i', '/^ServerAdmin you@example.com/s/^/#/g', '/etc/apache2/httpd.conf'] & FG

    ## Set MPM. WARNING: This choice of MPM precludes a default PHP setup.

    sed['-i', '/^LoadModule mpm_prefork_module /s/^/#/g', '/etc/apache2/httpd.conf'] & FG
    sed['-i', '/^LoadModule mpm_worker_module /s/^/#/g', '/etc/apache2/httpd.conf'] & FG
    sed['-i', '/^#LoadModule mpm_event_module /s/^#//g', '/etc/apache2/httpd.conf'] & FG

    ## Disable status module.
    sed['-i', '/^LoadModule status_module /s/^/#/g', '/etc/apache2/httpd.conf'] & FG

    ## TODO: Generate ServerName from hostname.
    ## (printf["ServerName " + environ['HOSTNAME']] | tee['/etc/apache2/conf.d/fqdn.conf'])()

    ## TODO: KeepAlive on

    ln['-sf', '/dev/stdout', '/var/log/apache2/access.log'] & FG
    ln['-sf', '/dev/stderr', '/var/log/apache2/error.log'] & FG

    httpd['-t', '-V'] & FG

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