#!/usr/bin/env python3

import os
import subprocess
import argparse
import shutil
import sys
from typing import Dict, Any, Optional, List, Set, Tuple

def get_repo_name(git_url: str) -> str:
    if git_url.endswith('.git'):
        git_url = git_url[:-4]
    repo_name = git_url.split('/')[-1]
    if ':' in repo_name:
        repo_name = repo_name.split(':')[-1]
    return repo_name

def get_repo_status(repo: Dict[str, str]) -> Dict[str, Any]:
    """
    Returns a dictionary with repository status information.
    """
    parent_dir = repo['path']
    git_url = repo['git_url']
    repo_name = get_repo_name(git_url)
    full_repo_path = os.path.join(parent_dir, repo_name)
    exists = os.path.isdir(full_repo_path)
    is_git_repo = os.path.isdir(os.path.join(full_repo_path, '.git'))
    existing_git_url = None
    if is_git_repo:
        existing_git_url = get_existing_remote_url(full_repo_path)
    return {
        'parent_dir': parent_dir,
        'git_url': git_url,
        'repo_name': repo_name,
        'full_repo_path': full_repo_path,
        'exists': exists,
        'is_git_repo': is_git_repo,
        'existing_git_url': existing_git_url
    }

def get_existing_remote_url(full_repo_path: str) -> Optional[str]:
    try:
        output = subprocess.check_output(
            ['git', '-C', full_repo_path, 'config', '--get', 'remote.origin.url']
        )
        return output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def run_git_command(repo_path: str, args: List[str], error_message: str) -> bool:
    try:
        subprocess.check_call(['git'] + args, cwd=repo_path)
        return True
    except subprocess.CalledProcessError:
        print(error_message)
        return False

def clone_repo(repo: Dict[str, str], force: bool = False) -> None:
    repo_status = get_repo_status(repo)
    parent_dir = repo_status['parent_dir']
    git_url = repo_status['git_url']
    repo_name = repo_status['repo_name']
    full_repo_path = repo_status['full_repo_path']
    exists = repo_status['exists']
    is_git_repo = repo_status['is_git_repo']
    existing_git_url = repo_status['existing_git_url']

    if exists:
        if force:
            # Remove the existing directory
            try:
                shutil.rmtree(full_repo_path)
                print(f"Removed existing directory {full_repo_path}")
                exists = False  # Directory has been removed
            except subprocess.CalledProcessError:
                print(f"Error removing directory {full_repo_path}, skipping clone")
                return
        elif is_git_repo and existing_git_url == git_url:
            print(f"Repository {repo_name} already exists and has the same remote, skipping")
            return
        elif is_git_repo:
            print(f"Repository {repo_name} already exists but has a different remote URL")
            return
        else:
            print(f"Directory {full_repo_path} exists but is not a git repository, skipping")
            return

    # Clone the repository
    if run_git_command(parent_dir, ['clone', git_url], f"Error cloning repository {repo_name}"):
        print(f"Cloned repository {repo_name} into {parent_dir}")

def pull_repo(repo: Dict[str, str], force: bool = False) -> None:
    repo_status = get_repo_status(repo)
    full_repo_path = repo_status['full_repo_path']
    repo_name = repo_status['repo_name']
    exists = repo_status['exists']
    is_git_repo = repo_status['is_git_repo']

    if exists and is_git_repo:
        if force:
            # Discard local changes
            if run_git_command(full_repo_path, ['stash'], f"Error stashing changes in {repo_name}"):
                run_git_command(full_repo_path, ['stash', 'drop'], f"Error dropping stash in {repo_name}")
        if run_git_command(full_repo_path, ['pull'], f"Error pulling repository {repo_name}, skipping"):
            print(f"Pulled latest changes for repository {repo_name}")
    elif exists:
        print(f"Directory {full_repo_path} exists but is not a git repository, skipping")
    else:
        print(f"Repository directory {full_repo_path} does not exist, skipping pull")

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='GitInit tool')
    parser.add_argument('settings_file', nargs='?', default='settings.txt', help='Settings file')
    parser.add_argument('--clone', '-c', action='store_true', help='Clones the repositories specified in the settings file.')
    parser.add_argument('--pull', '-p', action='store_true', help='Pulls the latest changes from the remote repository.')
    parser.add_argument('--force', '-f', action='store_true', help='Adds a flag to overwrite existing directories or discard local changes.')
    return parser.parse_args()

def get_dirs_and_repos_from_settings(settings_file: str) -> Tuple[Set[str], List[Dict[str, str]]]:
    dirs_to_create = set()
    git_repos = []
    stack = []
    indent_levels = []

    with open(settings_file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue  # skip empty lines
            # Get the leading whitespace (spaces or tabs)
            leading_whitespace = line[:len(line) - len(line.lstrip())]
            indent_length = len(leading_whitespace.expandtabs(4))  # Convert tabs to spaces (tab size = 4)
            content = line.strip()
            if not indent_levels:
                # This is the first line
                indent_levels.append(indent_length)
            elif indent_length > indent_levels[-1]:
                # Indentation increased
                indent_levels.append(indent_length)
            else:
                # Indentation decreased or same
                while indent_levels and indent_length < indent_levels[-1]:
                    indent_levels.pop()
                    stack.pop()
                if indent_levels and indent_length != indent_levels[-1]:
                    # Indentation level does not match any existing level, append new level
                    indent_levels.append(indent_length)
            # Adjust the stack to match the current indentation level
            while len(stack) > len(indent_levels) - 1:
                stack.pop()
            stack.append(content)
            # Now construct the path
            if content.endswith('.git') and (content.startswith('git@') or content.startswith('https://')):
                # This is a git repository
                # The parent path is the current stack
                path = os.path.join(*stack[:-1])
                path = os.path.expanduser(path) # Expand ~
                git_url = content
                # Ensure directory is added
                dirs_to_create.add(path)
                git_repos.append({
                    'path': path,
                    'git_url': git_url
                })
            else:
                # This is a directory
                path = os.path.join(*stack)
                path = os.path.expanduser(path) # Expand ~
                dirs_to_create.add(path)
    return dirs_to_create, git_repos

def main() -> None:
    # check for required external programs
    if not shutil.which('git'):
        print("Error: 'git' is not installed or not found in PATH. Please install 'git' before running this script.")
        sys.exit(1)

    args = get_args()
    settings_file = args.settings_file
    dirs_to_create, git_repos = get_dirs_and_repos_from_settings(settings_file)

    # Create directories
    for directory in sorted(dirs_to_create):
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory {directory}")
        else:
            print(f"Directory {directory} already exists")

    # Perform cloning if requested
    if args.clone:
        for repo in git_repos:
            clone_repo(repo, force=args.force)

    # Perform pulling if requested
    if args.pull:
        for repo in git_repos:
            pull_repo(repo, force=args.force)

if __name__ == '__main__':
    main()
