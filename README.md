[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Baseline-quebec/cpeq-infolettre-automatique)

# cpeq-infolettre-automatique

CPEQ Infolettre automatique
 
## Installing

To install this package, run:

```sh
pip install cpeq-infolettre-automatique
```

## Using
 
To serve this app, run:

```sh
docker compose up app
```

and open [localhost:8000](http://localhost:8000) in your browser.

Within the Dev Container this is equivalent to:

```sh
poe api
```

## Requirements

This project requires Python, [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) and/or Docker ([Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows users) to be installed.

## Usage

### Container app

To use the application as a container app, run `docker compose up app` and open [localhost:8000](http://localhost:8000) in your browser.

### Bare metal app

If not already done, install the package by running in the terminal `poetry install`.

Then run `poe api` in the terminal. The API will be available at [localhost:8000](http://localhost:8000).


## Contributing

### Prerequisites

<details>
<summary>1. Set up Git to use SSH</summary>

1. [Generate an SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key) and [add the SSH key to your GitHub account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
1. Configure SSH to automatically load your SSH keys. Add the following at the end of your `.ssh/config` file:
```
Host *
    AddKeysToAgent yes
    IgnoreUnknown UseKeychain
    UseKeychain yes
    ForwardAgent yes
```
</details>

<details>
<summary>2. Install Docker</summary>

[Install Docker Desktop](https://www.docker.com/get-started).
    - _Linux only_:
        - Export your user's user id and group id so that [files created in the Dev Container are owned by your user](https://github.com/moby/moby/issues/3206):
            ```sh
            cat << EOF >> ~/.bashrc
            export UID=$(id --user)
            export GID=$(id --group)
            EOF
            ```

</details>

<details>
<summary>3. Install VS Code</summary>

[Install VS Code](https://code.visualstudio.com/) and [VS Code's Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
</details>


### Development environments

<details>
<summary>Dev container environments</summary>

You can develop "remotely" inside a container using one of the following development environments:

1. ⭐️ _GitHub Codespaces_: click on _Code_ and select _Create codespace_ to start a Dev Container with [GitHub Codespaces](https://github.com/features/codespaces).
1. ⭐️ _Dev Container (with container volume)_: click on [Open in Dev Containers](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/Baseline-quebec/cpeq-infolettre-automatique) to clone this repository in a container volume and create a Dev Container with VS Code.
1. _Dev Container_: clone this repository, open it with VS Code, and run <kbd>Ctrl/⌘</kbd> + <kbd>⇧</kbd> + <kbd>P</kbd> → _Dev Containers: Reopen in Container_.
1. _PyCharm_: clone this repository, open it with PyCharm, and [configure Docker Compose as a remote interpreter](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html#docker-compose-remote) with the `dev` service.
1. _Terminal_: clone this repository, open it with your terminal, and run `docker compose up --detach dev` to start a Dev Container in the background, and then run `docker compose exec dev zsh` to open a shell prompt in the Dev Container.

</details>

<details>
<summary>Local development</summary>

To develop locally, you'll have to install manually some tools.
First, initialize a virtual environment for the project with
```poetry shell```
and then install the dependencies and the project with
```poetry install```

</details>


### Development tools

The following tools will be automatically installed by poetry to support development:

- _commitizen_: This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard to automate [Semantic Versioning](https://semver.org/) and [Keep A Changelog](https://keepachangelog.com/) with [Commitizen](https://github.com/commitizen-tools/commitizen).

- _pre-commit_: This project uses pre-commit hooks that enforces the submitted code to respect conventions and high quality standards.

- _pytest_: This project uses the `pytest` framework for unit testing.

- _ruff_: This project uses `ruff` to lint and automatically format code in order to maintain consistent code across all project and developpers.

- _mypy_: This project uses the static type checker `mypy` to enforce type annotation and spot bugs before they can happen.

We use the following integration tools:

- _github actions_: This project uses GitHub actions to execute verifications in the cloud before allowing to merge with the main branch.


### Development workflow

1. Open new branch.
1. Write code.
1. Write tests.
1. Run tests and linter with `poe test` and `poe lint`.
1. Commit code with `cz commit` and follow the instructions.
    1. Retry failed commit (after fixing) with `cz commit --retry`.
    1. *Only in emergencies*, commit with `git commit --no-verify`.
1. Push commits with `git push`.
1. When branch is fully functional, open a pull requests on GitHub and ask for a review.
    1. When approved, bump the versions with `cz bump`.
    1. Build the doc with `poe doc`.
    1. Push to GitHub one last time before merging.
1. Repeat.


### Good development practices

- Most if not all functions and methods should be tested.

- All functions, methods, modules and classes should have proper documentation.

- All functions and methods should be properly annotated.

- Commits should be atomic.

- Dependency injection should be favorized, and objects instantiation should be made at the latest possible moment.

- Always keep Separation of Concerns in mind.


### Developing tips and tricks

- Run `poe` from within the development environment to print a list of [Poe the Poet](https://github.com/nat-n/poethepoet) tasks available to run on this project.

- Run `poetry add {package}` from within the development environment to install a run time dependency and add it to `pyproject.toml` and `poetry.lock`. Add `--group test` or `--group dev` to install a CI or development dependency, respectively.

- Run `poetry update` from within the development environment to upgrade all dependencies to the latest versions allowed by `pyproject.toml`.

- Run `cz bump` to bump the app's version, update the `CHANGELOG.md`, and create a git tag.

- Many VSCode extensions exists to help you code better and faster. We recommend the following ones:
    - The "Python" extension and its suite ("Python", "Pylance", "Python Debugger")
    - The "ruff" extension: Automatically shows which linting and formatting rules are failing directly into the code. Tips: bind keyboard shortcuts to format and fix linting errors easily and quickly.
    - The "mypy" extension: Automatically shows which type annotation are invalid directly into the code. N.B.: the extension is fairly slow, at least on Windows.
    - The "Docker" extension.
    - The "DevContainer" extension.
    - The "Jupyter" extension: Allows you to edit and run notebooks directly in VS Code
