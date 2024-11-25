#!/usr/bin/env python3

import os
import subprocess
import argparse
from typing import List, Dict, Set, Tuple

class RepoInfo:
    def __init__(self, path: str, git_url: str):
        self.parent = path
        self.git = git_url
        self.name = get_repo_name(git_url)
        self.fpath = os.path.join(path, self.name)
        self.isdir = os.path.isdir(self.fpath)
        self.isgit = os.path.isdir(os.path.join(self.fpath, '.git'))

    def __repr__(self):
        return f"RepoStatus(parent={self.parent}, git={self.git}, name={self.name}, fpath={self.fpath}, isdir={self.isdir}, isgit={self.isgit})"

    def __str__(self):
        return f"Repository {self.name} in {self.parent} is{' not' if not self.isdir else ''} a directory and is{' not' if not self.isgit else ''} a git repository"

    def __eq__(self, other):
        return self.parent == other.parent and self.git == other.git and self.name == other.name and self.fpath == other.fpath and self.isdir == other.isdir and self.isgit == other.isgit

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.parent, self.git, self.name, self.fpath, self.isdir, self.isgit))

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def as_tuple(self):
        return self.parent, self.git, self.name, self.fpath, self.isdir, self.isgit

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> 'RepoInfo':
        return cls(d['parent'], d['git'], d['name'], d['fpath'], d['isdir'], d['isgit'])

    def to_dict(self) -> Dict[str, str]:
        return {
            'parent': self.parent,
            'git': self.git,
            'name': self.name,
            'fpath': self.fpath,
            'isdir': self.isdir,
            'isgit': self.isgit
        }

def get_repo_name(git_url: str) -> str:
    repo_name: str = git_url.rstrip('.git').split('/')[-1]
    if ':' in repo_name:
        repo_name: str = repo_name.split(':')[-1]
    return repo_name

def get_args() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='GitInit tool')
    parser.add_argument('settings_file', nargs='?', default='settings.txt', help='Settings file')
    parser.add_argument('--pull', '-p', action='store_true', help='Pulls the latest changes from the remote repository.')
    parser.add_argument('--forcepull', '-fp', action='store_true', help='Discards local changes and pulls the latest changes from the remote repository.')
    return parser.parse_args()

def get_dirs_and_repoinfos_from_settings(settings_file: str) -> Tuple[Set[str], List[RepoInfo]]:
    dirs_to_create: Set[str] = set()
    git_repos: List[RepoInfo] = []
    stack: List[str] = []
    with open(settings_file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue  # skip empty lines
            indent: int = len(line) - len(line.lstrip(' '))
            indent_level: int = indent // 4
            content: str = line.strip()
            # Adjust stack to match the current indent level
            while len(stack) > indent_level:
                stack.pop()
            stack.append(content)
            # Now construct the path
            if '.git' in content or content.startswith('git@') or content.startswith('https://'):
                # This is a git repository
                # The parent path is the current stack
                path: str = os.path.join(*stack[:-1])
                git_url: str = content
                # Ensure directory is added
                dirs_to_create.add(path)
                git_repos.append(RepoInfo(path, git_url))
            else:
                # This is a directory
                path: str = os.path.join(*stack)
                dirs_to_create.add(path)
    return dirs_to_create, git_repos

def create_directories(dirs_to_create: Set[str]) -> None:
    for directory in sorted(dirs_to_create):
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory {directory}")
        else:
            print(f"Directory {directory} already exists")

def clone_repo(repo: RepoInfo) -> None:
    if repo.isdir:
        if repo.isgit:
            try: # Get the remote URL
                output = subprocess.check_output(['git', '-C', repo.fpath, 'config', '--get', 'remote.origin.url'])
                existing_git_url = output.decode().strip()
                if existing_git_url == repo.git:
                    print(f"Repository {repo.name} already exists and has the same remote, skipping")
                else:
                    print(f"Repository {repo.name} already exists but has a different remote URL")
            except subprocess.CalledProcessError:
                print(f"Error checking remote URL for repository {repo.name}, skipping")
        else:
            print(f"Directory {repo.fpath} exists but is not a git repository, skipping")
    else:
        # Clone the repository
        try:
            subprocess.check_call(['git', 'clone', repo.git], cwd=repo.parent)
            print(f"Cloned repository {repo.name} into {repo.parent}")
        except subprocess.CalledProcessError:
            print(f"Error cloning repository {repo.name}")

def pull_repo(repo: RepoInfo, force: bool = False) -> None:
    if repo.isdir:
        if repo.isgit:
            try: # Perform git pull
                if force: # Discard local changes
                    subprocess.check_call(['git', 'stash'], cwd=repo.fpath)
                    subprocess.check_call(['git', 'stash', 'drop'], cwd=repo.fpath)
                subprocess.check_call(['git', 'pull'], cwd=repo.fpath)
                print(f"Pulled latest changes for repository {repo.name}")
            except subprocess.CalledProcessError:
                print(f"Error pulling repository {repo.name}, skipping")
        else:
            print(f"Directory {repo.fpath} exists but is not a git repository, skipping")
    else:
        print(f"Repository directory {repo.fpath} does not exist, skipping pull")

def main():
    args: argparse.Namespace = get_args()
    settings_file: str = args.settings_file
    if not os.path.isfile(settings_file):
        print(f"Settings file {settings_file} not found")
        return
    dirs_to_create, git_repos = get_dirs_and_repoinfos_from_settings(settings_file)
    create_directories(dirs_to_create)

    # Clone repositories
    for repo in git_repos:
        clone_repo(repo)
    # Pull updates if requested
    if args.pull or args.forcepull:
        for repo in git_repos:
            pull_repo(repo, args.forcepull)

if __name__ == '__main__':
    main()
