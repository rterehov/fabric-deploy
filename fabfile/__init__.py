# coding: utf-8

import os

from fabric.api import env, task

from .deploy import deploy


help_text = """
Reliably deploy web application to any number of machines simultaneously.

Usage:
    fab [-R] [-H] [<env>] <action> [<action>]

Options:
    -R ROLES, --roles=ROLES
                        comma-separated list of roles to operate on
    -H HOSTS, --hosts=HOSTS
                        comma-separated list of hosts to operate on
    env                 environment from list: develop, stage, production
                        (defaut: develop)
    action              space-separated list of actions
                        (use 'fab --list' to see all actions)

Examples:
    fab deploy          deploy on development servers
    fab deploy.update   update only changed files

You can see extended help for fab command.
Type 'fab --help' to view it.
"""
@task
def help():
    """Help"""
    print(help_text)


# Settings
env.project_name = ''
env.user = env.project_name
env.releases_dir = 'releases'
env.current = 'current'
env.python = 'python3.5'  # python 2.8
env.requirements = 'requirements.txt'
env.config_dir = 'config'
env.config_filename = 'development.py'
env.errors = []
env.warnings = []

ROOT = os.path.join('/home', env.user)

env.hosts = env.hosts or []

env.keep_releases = 5


def __init_env__():
    """Init environment settings"""

    env.project_root = os.path.join(ROOT, env.env)
    env.venv_name = '{}.{}'.format(env.env, env.project_name)
    env.venv_root = os.path.join(ROOT, '.virtualenvs', env.venv_name)

    env.releases_path = os.path.join(env.project_root, env.releases_dir)
    env.requirements = os.path.join(env.project_root, env.current,
                                    env.requirements)
    env.current_path = os.path.join(env.project_root, env.current)


@task
def production():
    """Setting up production environment"""
    env.env = 'prod'
    env.config_filename = 'production.py'
    __init_env__()


@task
def stage():
    """Setting up staging environment"""
    env.env = 'st'
    env.config_filename = 'stage.py'
    __init_env__()


@task
def develop():
    """Setting up development environment"""
    env.env = 'dev'
    env.config_filename = 'development.py'
    __init_env__()

develop()  # Use develop environment by default

