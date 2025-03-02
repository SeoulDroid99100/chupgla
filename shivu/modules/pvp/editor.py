# editor.py
from shivu import shivuu, xy
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json

# In-memory storage
user_teams = {}  # {user_id: {team_index: [pokemon_names]}}
editing_sessions = {}  # {user_id: {current_team: int, edit_msg_id: int}}

# Load Pokémon data
with open('pokemons.json') as f:
    POKE_DATA = json.load(f)

class TeamEditor:
    async def start_editor(self, user_id):
        """Initialize editor session"""
        # Initialize in-memory teams if not exists
        if user_id not in user_teams:
            saved = await xy.teams.find_one({'user_id': user_id})
            user_teams[user_id] = saved['teams'] if saved else [[] for _ in range(6)]
        
        # Initialize editing session
        editing_sessions[user_id] = {
            'current_team': 0,
            'edit_msg_id': None
        }
        
        await self.show_team_selection(user_id)

    async def show_team_selection(self, user_id):
        """Show team selection interface"""
        buttons = []
        for i in range(0, 6, 2):
            team1 = self.format_team_preview(user_id, i)
            team2 = self.format_team_preview(user_id, i+1)
            
            buttons.append([
                InlineKeyboardButton(team1, callback_data=f"selteam:{i}"),
                InlineKeyboardButton(team2, callback_data=f"selteam:{i+1}")
            ])
        
        buttons.append([InlineKeyboardButton("Close Editor", callback_data="closeeditor")])
        
        text = "**Team Editor**\nSelect a team to manage:"
        
        if editing_sessions[user_id]['edit_msg_id']:
            await shivuu.edit_message_text(
                user_id,
                editing_sessions[user_id]['edit_msg_id'],
                text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            msg = await shivuu.send_message(user_id, text, reply_markup=buttons)
            editing_sessions[user_id]['edit_msg_id'] = msg.id

    def format_team_preview(self, user_id, team_index):
        """Format team preview text"""
        team = user_teams[user_id][team_index]
        if not team:
            return f"Team {team_index+1}\n(Empty)"
        return f"Team {team_index+1}\n" + "\n".join(
            [f"• {p['name']}" for p in team[:3]] + 
            (["..."] if len(team) > 3 else [])
        )

    async def show_team_editor(self, user_id, team_index):
        """Show editor for specific team"""
        editing_sessions[user_id]['current_team'] = team_index
        current_team = user_teams[user_id][team_index]
        
        team_text = f"**Editing Team {team_index+1}**\n" + "\n".join(
            [f"• **{p['name']}**" for p in current_team]
        ) or "No Pokémon in team"
        
        buttons = [
            [InlineKeyboardButton("Add Pokémon", callback_data="addpokemon")],
            [InlineKeyboardButton("Remove Pokémon", callback_data="removepokemon")],
            [InlineKeyboardButton("Save Team", callback_data="saveteam")],
            [InlineKeyboardButton("Back to Teams", callback_data="backtoteams")]
        ]
        
        await shivuu.edit_message_text(
            user_id,
            editing_sessions[user_id]['edit_msg_id'],
            team_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def show_pokemon_selection(self, user_id):
        """Show Pokémon selection grid"""
        buttons = []
        all_pokemon = sorted(POKE_DATA.keys())
        
        for i in range(0, len(all_pokemon), 2):
            row = [
                InlineKeyboardButton(all_pokemon[i], callback_data=f"add:{all_pokemon[i]}"),
                InlineKeyboardButton(all_pokemon[i+1], callback_data=f"add:{all_pokemon[i+1]}")
            ] if i+1 < len(all_pokemon) else [
                InlineKeyboardButton(all_pokemon[i], callback_data=f"add:{all_pokemon[i]}")
            ]
            buttons.append(row)
        
        buttons.append([InlineKeyboardButton("Back", callback_data="backtoeditor")])
        
        await shivuu.edit_message_text(
            user_id,
            editing_sessions[user_id]['edit_msg_id'],
            "Select Pokémon to Add:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def show_remove_options(self, user_id):
        """Show Pokémon removal options"""
        team_index = editing_sessions[user_id]['current_team']
        team = user_teams[user_id][team_index]
        
        buttons = []
        for idx, pkmn in enumerate(team):
            buttons.append([
                InlineKeyboardButton(
                    f"Remove {pkmn['name']}",
                    callback_data=f"remove:{idx}"
                )
            ])
        
        buttons.append([InlineKeyboardButton("Back", callback_data="backtoeditor")])
        
        await shivuu.edit_message_text(
            user_id,
            editing_sessions[user_id]['edit_msg_id'],
            "Select Pokémon to Remove:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    async def handle_callback(self, client, query):
        """Process editor callbacks"""
        user_id = query.from_user.id
        data = query.data.split(":")
        
        if data[0] == "selteam":
            await self.show_team_editor(user_id, int(data[1]))
        
        elif data[0] == "addpokemon":
            await self.show_pokemon_selection(user_id)
        
        elif data[0] == "removepokemon":
            await self.show_remove_options(user_id)
        
        elif data[0] == "add":
            self.add_to_team(user_id, data[1])
            await self.show_team_editor(user_id, editing_sessions[user_id]['current_team'])
        
        elif data[0] == "remove":
            self.remove_from_team(user_id, int(data[1]))
            await self.show_team_editor(user_id, editing_sessions[user_id]['current_team'])
        
        elif data[0] == "saveteam":
            await self.save_team(user_id)
            await query.answer("Team saved successfully!")
            await self.show_team_selection(user_id)
        
        elif data[0] == "backtoteams":
            await self.show_team_selection(user_id)
        
        elif data[0] == "backtoeditor":
            await self.show_team_editor(user_id, editing_sessions[user_id]['current_team'])
        
        elif data[0] == "closeeditor":
            await self.cleanup_session(user_id)
            await query.answer("Editor closed")
        
        await query.answer()

    def add_to_team(self, user_id, pkmn_name):
        """Add Pokémon to in-memory team"""
        team = user_teams[user_id][editing_sessions[user_id]['current_team']]
        if len(team) < 6:
            team.append({"name": pkmn_name})

    def remove_from_team(self, user_id, index):
        """Remove Pokémon from in-memory team"""
        team = user_teams[user_id][editing_sessions[user_id]['current_team']]
        if 0 <= index < len(team):
            del team[index]

    async def save_team(self, user_id):
        """Save current team state to database"""
        await xy.teams.update_one(
            {'user_id': user_id},
            {'$set': {'teams': user_teams[user_id]}},
            upsert=True
        )

    async def cleanup_session(self, user_id):
        """Clean up editing session"""
        if user_id in editing_sessions:
            del editing_sessions[user_id]
        if user_id in user_teams:
            del user_teams[user_id]

# Initialize editor
team_editor = TeamEditor()

@shivuu.on_message(filters.command("editteam"))
async def start_editor(client, message):
    await team_editor.start_editor(message.from_user.id)

@shivuu.on_callback_query()
async def handle_editor_callbacks(client, query):
    await team_editor.handle_callback(client, query)
