 ## Intro
 - Use `uv`
 - Use Pylance in `strict` type checking mode
 - Each slice must be independent and decoupled, use `core/event_bus.py` to communicate. 
 - Use `commitizen` for commits

### Run Deus Vult
1. Install `uv` package manager [from here](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).
2. Install Python 3.12 if you don't have it.
```
uv python install 3.12
```
3. Activate virtual environment
```
source .venv/bin/activate
```
4. Running your Python script.
```
uv run main.py
```
5. Running the server
```
uv run uvicorn app:app --reload --loop uvloop
```

### Manage Dependencies
1. Adding a dependency
```
uv add httpx
```
2. Removing a dependency
```python
uv remove httpx
```
3. Locking depencendies
```
uv lock
```

### Manage Versions
- Use `cz commit` after adding changed files w/ `github add .`
- Use `git push --follow-tags` after to push the flags too.
- Use `cz bump` for meaningful version update, it will handle the rest.

### Deploying
- If you added dependencies, run `uv export --format requirements-txt --locked > requirements.txt`