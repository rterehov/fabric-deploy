# coding: utf-8

import os
import re

from datetime import datetime

from fabric.api import cd, env, run, prefix, parallel, task, execute, local
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

    if env.get('deploy_via') == 'copy':
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
    else:
        with cd(env.project_root):
            env.revision, _ = local(
                "git ls-remote %(repository)s %(branch)s" % env,
                capture=True
            ).split()

            run("if [ -d %(cached_copy)s ]; then "
                    "cd %(cached_copy)s "
                    "&& git fetch -q origin "
                    "&& git fetch --tags -q origin "
                    "&& git reset -q --hard %(revision)s "
                    "&& git submodule -q init "
                    "&& git submodule -q sync "
                    "&& export GIT_RECURSIVE=$([ ! \"`git --version`\" \\< \"git version 1.6.5\" ] "
                    "&& echo --recursive) "
                    "&& git submodule -q update --init $GIT_RECURSIVE "
                    "&& git clean -q -d -x -f; "
                "else "
                    "git clone -q -b develop git@github.com:elitsy/main.git %(cached_copy)s "
                    "&& cd %(cached_copy)s "
                    "&& git checkout -q -b deploy %(revision)s "
                    "&& git submodule -q init "
                    "&& git submodule -q sync "
                    "&& export GIT_RECURSIVE=$([ ! \"`git --version`\" \\< \"git version 1.6.5\" ] "
                    "&& echo --recursive) "
                    "&& git submodule -q update --init $GIT_RECURSIVE; "
                "fi" % env)

            run("cp -RPp %(cached_copy)s %(release_path)s "
                "&& (echo %(revision)s > %(release_path)s/REVISION)" % env)

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
    with prefix('. %(venv_root)s/bin/activate' % env):
        run('pip install -r %(requirements_path)s' % env)


@task
@parallel
def cleanup():
    """Clean up old releases"""

    with cd(env.releases_path):
        releases  = run('ls -x').split()
        releases = [r for r in releases if re.findall('^\d{14}$', r)]
        releases.sort()
        old = releases[:len(releases) - env.keep_releases]
        run('rm -rf {}'.format(' '.join(old)))


@task(default=True)
def deploy(*args, **kwargs):
    """Deploys your project"""

    release_label = datetime.now().strftime('%Y%m%d%H%M%S')
    env.release_path = os.path.join(env.releases_path, release_label)
    env.requirements_path = os.path.join(env.release_path, env.requirements)

    execute(setup)
    execute(update_code, path=env.release_path)
    execute(requirements)

    with cd(env.project_root):
        run('rm -f {current} && ln -s {release} {current}'.format(
            current=env.current,
            release=env.release_path,
        ))

    with cd(env.current_path), cd(env.config_dir):
        run('ln -s %(config_filename)s local.py' % env)

    execute(cleanup)
