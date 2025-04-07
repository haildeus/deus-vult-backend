# Wednesday plan:
- Set up service & endpoints for elements + recipe mixing
- Create API endpoints within infinite craft endpoints
- Pass telegram client within UoW

# Database
- Add indexes for the faster queries
- Upload the recipes and ingredients

## Adding combinations
1) Receive combination. 
2) Check progress to see if user has access to these elements.
3) Check if the combination is saved.

2) If it does:
- Respond with combination
- Update the progress

3) If it doesn't:
- Query the Gemini API
- Respond with the result
- Save to the database
- Update user progress

#### More on combos:
- Move elements_router.py to craft_router.py
- Create craft_orchestration.py where I'm going to orchestrate info.