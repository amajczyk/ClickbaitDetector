# pracaInzynierska

[praca](https://www.overleaf.com/project/659735d445dd668456c79553)

[Link to documentation](https://wutwaw-my.sharepoint.com/:w:/g/personal/01161500_pw_edu_pl/ETADAYVBpbpLki29IliMYjABbO4fgS3Eeopmss1XI3Jsqg?e=m0sXOV)


## Quick instructions on how to use Poetry

1. Install the package:

   1. When on Linux CLI use `curl -sSL https://install.python-poetry.org | python3 -`

   2. When on Powershell use `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -`

2. Add poetry path to your `$PATH` variable: `export PATH=$PATH:"/home/{YOUR USERNAME}/.local/bin/"`

3. Cd to our repo and run `poetry shell`

4. Make sure you've performed `git pull` and have `poetry.lock` and `pyproject.toml` files under its root dir

5. Run `poetry install`

6. Now, we're synced. When you want to add a dependency, run `poetry add <PACKAGE NAME>` and **commit your files to github**
