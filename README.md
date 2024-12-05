# GitInit
GitInit is a simple tool to help you migrate your complicated project directories and keep them up to date. It will automatically clone or pull the repos according to a directory structure specified in settings.txt.
## Dependencies
This tool depends on the following external programs:
1. git (can be installed via `sudo apt install git` on Ubuntu)
## Usage
1. Install dependencies mentioned above.
1. Create a symbolic link to the script in your path. For example, you can run `ln -s /path/to/gitinit.py /usr/local/bin/gitinit` to create a symbolic link in `/usr/local/bin/`.
1. Create a settings.txt in the following format:
    ```
    base_folder_1
        git@addr:example1.git
        folderA
            https://git.addr/example2.git
            sub1
                git@addr:example3.git
            sub2
                git@addr:example4.git
                https://git.addr/example5.git
        folderB
            sub1
                https://git.addr/example6.git
            sub2
        folderC
    base_folder_2
        git@addr:example7.git
    ```
    Note that `base_folder_1` and `base_folder_2` are *absolute* paths, whereas folders inside them are relative paths. There can be multiple root level folders specified in the same file like this.
1. Sort out `git` permissions / passwords or create ssh keys, as this tool will run `git clone` and `git pull` commands for you.
1. Run `python3 gitinit.py settings.txt --clone`. The tool will:
    - Automatically create the directories for you. If a directory already exists, it will skip the creation.
    - Automatically run `git clone` commands for you. If a directory already contains a git repository with the same remote, it will skip the cloning.
    - To force clone, you should run `python3 gitinit.py settings.txt --clone --force`. It is equivalent of running `rm -rf` on the directory and then cloning the repository.
    - You can use both `https` and `ssh` links. According to the `settings.txt` file above, the created folder structure will be:
        - base_folder_1
            - example1
            - folderA
                - example2
                - sub1
                    - example3
                - sub2
                    - example4
                    - example5
            - folderB
                - sub1
                    - example6
                - sub2
            - folderC
        - base_folder_2
            - example7
1. To keep the directory structures up to date, run `python3 gitinit.py settings.txt --pull`. 
    - The tool will automatically run `git pull` commands for you inside each git directory specified. On error, the tool will skip the directory.
    - To force pull and discard local changes, you should run `python3 gitinit.py settings.txt --pull --force`. It is equivalent of running `git stash` and then `git stash drop`, followed by `git pull`.

Note that if `settings.txt` is in the same folder as the script, you can omit it in the command.
## Parameters
| Parameter | Shorthand | Description |
| --- | --- | --- |
| `--clone` | `-c` | Clones the repositories specified in the settings file. |
| `--pull` | `-p` | Pulls the latest changes from the remote repository. |
| `--force` | `-f` | Adds a flag to overwrite existing directories or discard local changes. |
| `--help` | `-h` | Shows the help message. |