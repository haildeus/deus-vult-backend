## 1 Game
- Characters: contains "save files" for the users participating in the game, these are their characters.
- Clans: contains all the chats participating in the game. Each clan can be mapped back to a particular chat.

# 2 Telegram
## 2.1 Creating a clan pipeline
1. Bot joins the group.
2. Check if there's a clan associated with the chat.
- If not, send a message to activate. Listen to callback query to extract chat_instance and activate the clan.
- If there is, proceed.
3. Create characters (w/o overwriting) for available participants.
4. Associate characters to the created clan.

## 2.2 Listening to reactions
1. Dispatcher catches the update.
2. Goes through checks:
- Valid reaction
- Valid clan
- Valid user
3. Update the state:
- Asserts to check the legitimacy of changes
- Change the hp/mana for the users
