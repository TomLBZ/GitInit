#!/usr/bin/env python3

from gitinit import get_repo_name, get_args, get_dirs_and_repos_from_settings

if __name__ == '__main__':
    # called like python3 test.py repo_name
    print(get_repo_name("git@addr:example3.git"))
    print(get_repo_name("https://git.addr/example2.git"))
    print(get_args())
    print(get_dirs_and_repos_from_settings('settings.txt'))