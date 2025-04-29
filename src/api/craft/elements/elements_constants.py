from src.api.craft.elements.elements_schemas import ElementBase

VOID = ElementBase(name="Void", emoji="⚫", object_id=0)

# --- Starting Elements ---
FIRE = ElementBase(name="Fire", emoji="🔥", object_id=1)
WATER = ElementBase(name="Water", emoji="💧", object_id=2)
EARTH = ElementBase(name="Earth", emoji="🌍", object_id=3)
WIND = ElementBase(name="Wind", emoji="💨", object_id=4)

INIT_ELEMENTS = [VOID, FIRE, WATER, EARTH, WIND]
STARTING_ELEMENTS = [FIRE, WATER, EARTH, WIND]
