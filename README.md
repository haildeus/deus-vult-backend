 ## Intro
 - Use `uv`
 - Use Pylance in `strict` type checking mode
 - Each slice must be independent and decoupled, use `core/event_bus.py` to communicate. 

## How-to
1. Install `uv` package manager [from here](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).
2. Install Python 3.13 if you don't have it.
```
uv python install 3.13
```
3. Running your Python script.
```
uv run main.py
```
### How to Manage Dependencies
1. Adding a dependency
```
uv add httpx
```
2. Removing a dependency
```python
uv remove httpx
```

## Architecture

We're using vertical slice architecture. All the files for a single use case are grouped inside one folder. So, the cohesion for a single use case is very high. This simplifies the development experience. It's easy to find all the relevant components for each feature since they are close together.

### LLM/GenAI Integration - Unfinished
- [ ] Generate characters for the users.
- [ ] Generate storyline of the event.
- [ ] Generate the text highlights of the battle.
- [ ] Medival LoRA picture generation with *some* personalization.

### Pre-deployment
- [ ] Diskcache
- [ ] Testing
- [ ] Docker container.

### Nice Things
- [ ] Chroma embeddings for search
