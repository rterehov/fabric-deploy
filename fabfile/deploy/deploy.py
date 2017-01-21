# coding: utf-8

import os

from datetime import datetime

from fabric.api import cd, env, run, prefix, parallel, task, execute
from fabric.operations import put
from fabric.contrib.project import rsync_project


@task
@parallel
def setup():
    """Prepares servers for deployment"""

    run('mkdir -pv {}'.format(env.releases_path))


@task
@parallel
def update_code(path=None):
    """Copies your project for the remote servers"""

    remote_dir = path or env.current_path

    with cd(env.project_root):
        run('mkdir -p %(remote_dir)s' % locals())

    print("Sync {} -> {}".format('.', remote_dir))
    rsync_project(
        remote_dir=remote_dir,
        local_dir='.',
        exclude=(
            "local.py",
            "*_local.py",
            "*.pyc",
            ".git",
            ".idea",
            "__pycache__",
            ".gitignore",
            ".venv",
            "fabfile",
        ),
        delete=False,
    )    


@task
@parallel
def requirements():
    """Install packages and libraries from dependencies"""

    run('if [ ! -d "{venv_path}" ]; '
        'then virtualenv -p {python} {venv_path}; '
        'fi'.format(
            venv_path=env.venv_root,
            python=env.python
        )
    )
    with prefix('. {}/bin/activate'.format(env.venv_root)):
        run('pip install -r %(requirements)s' % env)


@task(default=True)
def deploy(*args, **kwargs):
    """Deploys your project"""

    release_label = datetime.now().strftime('%Y%m%d%H%M%S')
    env.release_path = os.path.join(env.releases_path, release_label)
    env.requirements = os.path.join(env.release_path, env.requirements)

    execute(setup)
    execute(update_code, path=env.release_path)
    execute(requirements)

    with cd(env.project_root):
        run('rm -f {current} && ln -s {release} {current}'.format(
            current=env.current,
            release=env.release_path,
        ))

    with cd(env.current):
        run('cd %(config_dir)s && ln -s %(config_filename)s local.py'.
            format(env))
