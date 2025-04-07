## 1. Running Locally
 - Use `uv`
 - Use Pylance in `strict` type checking mode
 - Each slice must be independent and decoupled, use `core/event_bus.py` to communicate. 
 - Use `commitizen` for commits

### 1.1 Start Server
1. Install `uv` package manager [from here](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).
2. Install Python 3.12 if you don't have it.
```
uv python install 3.12
```
3. Activate virtual environment
```
source .venv/bin/activate
```
4. Create .env file from .env.example and fill out the data.
5. Running your Python script.
```
uv run main.py
```
6. Running the server
```
uv run uvicorn app:app --reload --loop uvloop
```

### 1.2 Manage Dependencies
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

### 1.3 Manage Versions
- Use `cz commit` after adding changed files w/ `github add .`
- Use `git push --follow-tags` after to push the flags too.
- Use `cz bump` for meaningful version update, it will handle the rest.

## 2. Deploying
- We're deploying to Google App Engine.
- Don't forget to log into your account and init it.
```
gcloud init
```
- If the project is not set, please set it.

### 2.1 Manage Dependencies 
- If you added dependencies, run `uv export --format requirements-txt --locked > requirements.txt`
