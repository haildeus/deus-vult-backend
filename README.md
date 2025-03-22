## How to Run
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
Every dependency is saved within `pyproject.toml`.

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

## Checklist
### Telegram Integration - Unfinished
- [ ] Sending polls to choose community we're invading. Summing the results of the decision.
    - DONE: poll sending.
    - DONE: Storing the polls data.
    - Getting results of the poll.
- [ ] Tracking getting added to a new community. Extracting all the relevant messages from the community. Save to SQLite.
    - Create update handlers to track these events.
    - Once the bot appears in a new community, it needs to parse all available messages.
    - It also needs to check if it has all the required permissions.
- [X] Send a photo with text caption to the group chat.


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