# 10.014: Computational Thinking for Design - 1D Project
# Cohort 10 Group 9
# Lin Xi (1005145), Liu Renhang (1004873), Sharlene Chew Shi Ying (1005328), Lim Fuo En (1005125)

# All the data of the game. All these information and data are obtained from smogon.com and bulbapedia.bulbagarden.net
from pokemon import Pokemon
from base import Factory
import random

POKE_DB_PATH = 'pokemons.json'
poke_fac = Factory(Pokemon, POKE_DB_PATH)

pokemon_list = ['snorlax', 'lucario', 'salamence', 'tentacruel', 'rhyperior', 'tyranitar', 'volcarona', 'gengar', 'charizard', 'blastoise', 'venusaur', 'electivire', 'gardevoir', 'mamoswine', 'garchomp', 
'hydreigon', 'metagross', 'sylveon']
moves_list = ['Curse', 'Body_Slam', 'Rest', 'Earthquake', 'Swords_Dance', 'Meteor_Mash', 'Close_Combat', 'Bullet_Punch', 'Dragon_Dance', 'Double_Edge', 'Dragon_Claw', 'Aerial_Ace', 'Scald', 'Toxic', 
'Sludge_Bomb', 'Dazzling_Gleam', 'Stone_Edge', 'Megahorn', 'Ice_Punch', 'Rock_Slide', 'Crunch', 'Fire_Punch', 'Quiver_Dance', 'Flamethrower', 'Bug_Buzz', 'Roost', 'Shadow_Ball', 'Sludge_Wave', 
'Focus_Blast', 'Thunderbolt', 'Fire_Blast', 'Air_Slash', 'Dragon_Pulse', 'Hydro_Pump', 'Ice_Beam', 'Aura_Sphere', 'Leech_Seed', 'Leaf_Storm', 'Psychic', 'Moonblast', 'Will_O_Wisp', 'Ice_Shard', 
'Icicle_Crash', 'Knock_Off', 'Aqua_Tail', 'Draco_Meteor', 'Dark_Pulse', 'Charge_Beam', 'Thunder_Punch', 'Hyper_Voice', 'Mystical_Fire']

# Functions of the game
def view_move(): # Prompts the player to choose a move so that he can view the details of the move.
	# Move details
	Curse = {'Power': 0, 'Type': 'Ghost', 'Category': 'Status', 'PP': 10, 'Accuracy': 0, 'Priority': 0, 'Description': 'Raises Attack and Defense stats by 1 stage each, reduces Speed stat by 1 stage.'}
	Body_Slam = {'Power': 85, 'Type': 'Normal', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 30% chance of paralysis.'}
	Rest = {'Power': 0, 'Type': 'Psychic', 'Category': 'Status', 'PP': 10, 'Accuracy': 0, 'Priority': 0, 'Description': 'Sleeps for 2 turns, but fully restores HP and clears status effects.'}
	Earthquake = {'Power': 100, 'Type': 'Ground', 'Category': 'Physical', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'} 
	Swords_Dance = {'Power': 0, 'Type': 'Normal', 'Category': 'Status', 'PP': 20, 'Accuracy': 0, 'Priority': 0, 'Description': 'Raises Attack stat by 2 stages.'}
	Meteor_Mash = {'Power': 90, 'Type': 'Steel', 'Category': 'Physical', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Deals damage and 20% chance to raise Attack stat by 1 stage.'}
	Close_Combat = {'Power': 120, 'Type': 'Fighting', 'Category': 'Physical', 'PP': 5, 'Accuracy': 1, 'Priority': 0, 'Description': 'Lowers Defense and Sp_Def stats by 1 stage each.'}
	Bullet_Punch = {'Power': 40, 'Type': 'Steel', 'Category': 'Physical', 'PP': 30, 'Accuracy': 1, 'Priority': 1, 'Description': 'Deals damage, usually moves before most other moves.'}
	Dragon_Dance = {'Power': 0, 'Type': 'Dragon', 'Category': 'Status', 'PP': 20, 'Accuracy': 0, 'Priority': 0, 'Description': 'Raises Attack and Speed stats by 1 stage each.'} 
	Double_Edge = {'Power': 120, 'Type': 'Normal', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and receives recoil damage of 1/3 of target's lost HP from damage."} 
	Dragon_Claw = {'Power': 80, 'Type': 'Dragon', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'} 
	Aerial_Ace = {'Power': 60, 'Type': 'Flying', 'Category': 'Physical', 'PP': 20, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage, never misses.'} 
	Scald = {'Power': 80, 'Type': 'Water', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 30% chance to burn the target.'}
	Toxic = {'Power': 0, 'Type': 'Poison', 'Category': 'Status', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Badly poisons the target, and if the user is a Poison type Pokemon, this move will always hit the target.'}
	Sludge_Bomb = {'Power': 90, 'Type': 'Poison', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 30% chance to poison the target.'}
	Dazzling_Gleam = {'Power': 80, 'Type': 'Fairy', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'}
	Stone_Edge = {'Power': 100, 'Type': 'Rock', 'Category': 'Physical', 'PP': 5, 'Accuracy': .8, 'Priority': 0, 'Description': 'Deals damage, has a high critical hit ratio.'}
	Megahorn = {'Power': 120, 'Type': 'Bug', 'Category': 'Physical', 'PP': 10, 'Accuracy': .85, 'Priority': 0, 'Description': 'Deals damage.'}
	Ice_Punch = {'Power': 75, 'Type': 'Ice', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Freeze the target.'}
	Rock_Slide = {'Power': 75, 'Type': 'Rock', 'Category': 'Physical', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Deals damage and 30% chance to flinch the target.'}
	Crunch = {'Power': 80, 'Type': 'Dark', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and 20% chance to lower target's Defense stat by 1 stage."}
	Fire_Punch = {'Power': 75, 'Type': 'Fire', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Burn the target.'}
	Quiver_Dance = {'Power': 0, 'Type': 'Bug', 'Category': 'Status', 'PP': 20, 'Accuracy': 0, 'Priority': 0, 'Description': "Raises the user's Sp_Atk, Sp_Def and Speed stats by 1 stage each."}
	Flamethrower = {'Power': 90, 'Type': 'Fire', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Burn the target.'}
	Bug_Buzz = {'Power': 90, 'Type': 'Bug', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and 10% chance to lower the target's Sp_Def stat by 1 stage."}
	Roost = {'Power': 0, 'Type': 'Flying', 'Category': 'Status', 'PP': 10, 'Accuracy': 0, 'Priority': 0, 'Description': 'User restores 50% of their max HP, half up.'}
	Shadow_Ball = {'Power': 80, 'Type': 'Ghost', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and 20% chance of lowering target's Sp. Def stat by 1 stage."}
	Sludge_Wave = {'Power': 95, 'Type': 'Poison', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance of Poisoning the target.'}
	Focus_Blast = {'Power': 120, 'Type': 'Fighting', 'Category': 'Special', 'PP': 5, 'Accuracy': .7, 'Priority': 0, 'Description': "Deals damage and 10% chance of lowering target's Sp. Def stat by 1 stage."}
	Thunderbolt = {'Power': 90, 'Type': 'Electric', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Paralyse the target.'}
	Fire_Blast = {'Power': 110, 'Type': 'Fire', 'Category': 'Special', 'PP': 5, 'Accuracy': .85, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Burn the target.'} 
	Air_Slash = {'Power': 75, 'Type': 'Flying', 'Category': 'Special', 'PP': 15, 'Accuracy': .9, 'Priority': 0, 'Description': 'Deals damage and 30% chance to Flinch the target.'}
	Dragon_Pulse = {'Power': 85, 'Type': 'Dragon', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'}
	Hydro_Pump = {'Power': 110, 'Type': 'Water', 'Category': 'Special', 'PP': 5, 'Accuracy': .8, 'Priority': 0, 'Description': 'Deals damage.'}
	Ice_Beam = {'Power': 90, 'Type': 'Ice', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Freeze the target.'}
	Aura_Sphere = {'Power': 80, 'Type': 'Fighting', 'Category': 'Special', 'PP': 20, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and this move will always hit.'}
	Leech_Seed = {'Power': 0, 'Type': 'Grass', 'Category': 'Status', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Target loses 1/8 of its maximum HP, and user gains that same amount of HP at the end of every turn.'}
	Leaf_Storm = {'Power': 130, 'Type': 'Grass', 'Category': 'Special', 'PP': 5, 'Accuracy': .9, 'Priority': 0, 'Description': "Deals damage and lowers the user's Sp_Atk stat by 2 stages."}
	Psychic = {'Power': 90, 'Type': 'Psychic', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and 10% chance to lower target's Sp_Def stat 1 stage."}
	Moonblast = {'Power': 95, 'Type': 'Fairy', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and 30% chance to lower target's Sp_Atk stat by 1 stage."}
	Will_O_Wisp = {'Power': 0, 'Type': 'Fire', 'Category': 'Status', 'PP': 15, 'Accuracy': .85, 'Priority': 0, 'Description': 'Burns the target.'}
	Ice_Shard = {'Power': 40, 'Type': 'Ice', 'Category': 'Physical', 'PP': 30, 'Accuracy': 1, 'Priority': 1, 'Description': 'Deals damage, usually moves before most other moves.'}
	Icicle_Crash = {'Power': 85, 'Type': 'Ice', 'Category': 'Physical', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Deals damage and 30% chance to flinch the target.'}
	Knock_Off = {'Power': 65, 'Type': 'Dark', 'Category': 'Physical', 'PP': 20, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'}
	Aqua_Tail = {'Power': 90, 'Type': 'Water', 'Category': 'Physical', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': 'Deals damage.'}
	Draco_Meteor = {'Power': 130, 'Type': 'Dragon', 'Category': 'Special', 'PP': 5, 'Accuracy': .9, 'Priority': 0, 'Description': "Deals damage and then lowers the user's Sp_Atk stat by 2 stages."}
	Dark_Pulse = {'Power': 80, 'Type': 'Dark', 'Category': 'Special', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 20% chance to flinch the target.'}
	Charge_Beam = {'Power': 50, 'Type': 'Electric', 'Category': 'Special', 'PP': 10, 'Accuracy': .9, 'Priority': 0, 'Description': "Deals damage and 70% chance to raise user's Sp_Atk stat by 1 stage."}
	Thunder_Punch = {'Power': 75, 'Type': 'Electric', 'Category': 'Physical', 'PP': 15, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage and 10% chance to Paralyse the target.'}
	Hyper_Voice = {'Power': 90, 'Type': 'Normal', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': 'Deals damage.'}
	Mystical_Fire = {'Power': 75, 'Type': 'Fire', 'Category': 'Special', 'PP': 10, 'Accuracy': 1, 'Priority': 0, 'Description': "Deals damage and lowers target's Sp_Atk stat by 1 stage."}
  
	print()
	move_name_string = input("Please type in the name of the move (exactly as displayed, excluding the '') to view its details, type 'next' if you no longer wish to view the moves: ")
	print()

	while move_name_string.lower() != 'next':
		# Checks if an invalid input has been entered (invalid input means not the exact name of the move as displayed)
		while move_name_string not in moves_list and move_name_string != 'next':
			move_name_string = input("Invalid move! Please type in the name of the move (exactly as displayed, case and space sensitive, excluding the ''), or type in 'next' to return to the Pokemon list: ")
			print()

		# Displays the details of each move, vars() syntax is from https://www.daniweb.com/programming/software-development/threads/111526/setting-a-string-as-a-variable-name
		if move_name_string != 'next': # In case the user types 'next' previously
			move_name = vars()[move_name_string]
			print(f'''{move_name_string} - Type: {move_name['Type']} | Category: {move_name['Category']} | Power: {move_name['Power']} | Accuracy: {int(move_name['Accuracy'] * 100)}% | PP: {move_name['PP']}\nDescription: {move_name['Description']}''')
			print()
			move_name_string = input("Type 'next' if you no longer wish to view the moves and go back to the Pokemon list. Else, type in the name of the move to view its details: ")
			print()

# Displays the current status and HP of the Pokemon in battle
def display_hp_status():
	print(f'''{player_1_pokemon.player[1]}''')
	print('_________________________')
	print(f'''{player_1_pokemon.name}\nHP: {player_1_pokemon.hp}/{player_1_pokemon.max_hp}''') # Prints out the current HP of the Pokemon
	print(f'''Status: {player_1_pokemon.status}''')
	print('_________________________')
	print()
	print(f'''{player_2_pokemon.player[1]}''')
	print('_________________________')
	print(f'''{player_2_pokemon.name}\nHP: {player_2_pokemon.hp}/{player_2_pokemon.max_hp}''') # Prints out the current HP of the Pokemon
	print(f'''Status: {player_2_pokemon.status}''')
	print('_________________________')
	print()
	print('_________________________________________________________________')

# To check if any Pokemon has died/fained/HP is 0 
def check_0_hp(pokemon):
	if pokemon.hp <= 0:
		print()
		display_hp_status()
		print()
		print(f"{pokemon.player[1]}'s {pokemon.name} has fainted, {pokemon.opp.player[1]}'s {pokemon.opp.name} wins!")
		print()
		return True

# Prints out the Magikarp information (Easter Egg)
# The ASCII art is from https://textart.io/art/AYZk5vNANG1Ek_avIk8fOAeF/magikarp-pokemon
def print_magikarp():
	print('_________________________________________________________________')
	print('''
		                                 __.--.._,-'""-.
                              ,-' .' ,'  .-"''-.`.       .--.
                            ,'    |  |  '`-.    \ \       `-.|
                           /       .   /    `.   \ \        ||
                          /         `..`.    `.   \ .       ||
                         /        . .    `.    \   . .      '.
                ."-.    .  ,""'-. | |      \    \   `.`.__,'.'
                 `. `. .   |     `. |       \    .    `-..-'
       _______     .  `|   |   '   .'        .   |...--._
       `.     `"--.'   '    .      | .        .  |""''"-._"-._
         `.             \    `-._..'. .       |  |---.._  `-.__"-..
    -.     `.           |\           `.`      |  |'`-.  `-._   +"-'
    `.`.     `-.        | `            .`.       | `. `.    `,"
      `.`.      `.      |  '.           ` `      `.  \  `   /
      | `.`.    __`.    |`/  `.     ...  `.`.     |   `.   .
      |   \ .  `._      | `. / `. .'.' |   \ \    |     \  |
      |.   ` \    `-.   |   \   .'.'/' |    \ \   |      ._'
      | `.  `.\      `. |    \ / , '.  |_    . \  '-.
     ,     .  .\       `|     . ' / |  | `-...\ \'   `._
     `.     `.  \       |.    '/ .  |  |       ' .      `-.
      .`._    \` \      | `. /'  '  |  |       | |       ,.'
       .  `-.  \`.\    ,|   //  '   |  |__  .' | |      |
       |     `._`| `--' `  //  .    |  '  `"  /| |   . -'
       '        `|       `//   '    |   .    / | |   |
      /....._____|       //   .  ___|   |   /  | |  ,|
     .         _.'      /, _.--"'-._ `".| ,'   | |.'
     |      _,' / ___   `-'.        `. _|'     |,
     |  _,-"  ,'.'   `-.._  `.      _,'         `
     '-"   _,','          "- ....--'
    /  _.-"_.'
   /_,'_,-'
 .'_.-'
 '"
			''')
	print('Behold. Magikarp, the Pokemon who made the strongest move in existence, Splash, famous.')
	print()
	print('Just kidding. It actually has one of the lowest base stats in the actual Pokemon game. We are not going to add Magikarp to our game.')
	print()
	print('_________________________________________________________________')
	print()

# The actual game
# The Pokemon ASCII art right below is from https://www.asciiart.eu/video-games/pokemon
print('''
  _ __   ___ | | _____ _ __ ___   ___  _ __       ___      __      _____   _____          _____
 | '_ \ / _ \| |/ / _ \ '_ ` _ \ / _ \| '_ \     |   \    /  \       |       |     |     |
 | |_) | (_) |   <  __/ | | | | | (_) | | | |    |___|   /____\      |       |     |     |_____
 | .__/ \___/|_|\_\___|_| |_| |_|\___/|_| |_|    |   |  /      \     |       |     |     |
 |_|                                             |___/ /        \    |       |     |____ |_____
	''')

print()

# Gets the names of both players
player_1_name = input("Player 1, please input your name: ")
print(f'Hello, {player_1_name}!')
player_2_name = input("Player 2, please input your name: ")
print(f'Hello, {player_2_name}!')

# To allow the players to view the details and information of each move and Pokemon
print()
print('Each player shall choose one Pokemon and battle it out! The battle ends when one Pokemon faints/has 0 HP.')
print('Before both of you choose your Pokemon, please have a look at the details and information of the Pokemon.')

trigger = True # So that the while loop below (to display the Pokemon list) can keep running until the user inputs 'continue'.

while trigger:
	print()
	print('''Pokemons available:\n\n- Snorlax (The Sleeping Giant)\n- Lucario (The UFC Fighter)\n- Salamence (The European Dragon)\n- Tentacruel (The Box Jellyfish)\n- Rhyperior (The Boulder Rhino)\n- Tyranitar (The Tyrannosarus Rex)\n- Volcarona (The Fire Bug)\n- Gengar (The Original Ghost)\n- Charizard (The Fire Dragon)\n- Blastoise (The Cannon Tortoise)\n- Venusaur (The Poison Rafflesia)\n- Electivire (The Electric Fighter)\n- Gardevoir (The Beautiful Sorcerer)\n- Mamoswine (The Ice Mammoth)\n- Garchomp (The Land Shark)\n- Hydreigon (The Black Dragon)\n- Metagross (The Computer Monster)\n- Sylveon (The Weird Eeveelution)\n- Magikarp (The Strongest and Most Legendary Pokemon in all of Existence)''')
	print()
	user_input = input("Please type in the name of a Pokemon to look at its information. Type in 'continue' to move on with the game: ")
	print()

	# Prints out the dictionary containing the main details of each Pokemon
	if user_input.lower() in pokemon_list:
		print(poke_fac.make(user_input, player = (3))) # So that whatever Pokemon the player chooses here (just to view its information) will not be assigned to any of the players in the actual battle
		view_move()

	elif user_input.lower() == 'magikarp':
		print_magikarp()
		user_input = input('Please input any key to continue: ')

	elif user_input.lower() == 'continue':
		trigger = False
		
	else:
		user_input = input("Invalid input! Input any key to continue: ")
		print()

print("Now, it's time to choose your Pokemon!")
# The following quote is from https://bulbapedia.bulbagarden.net/wiki/Karen/Quotes#:~:text=%22Strong%20Pok%C3%A9mon.,to%20win%20with%20their%20favorites.
print('"Strong Pokemon. Weak Pokemon. That is only the selfish perception of people. Truly skilled trainers should try to win with their favorites." - Karen, Pokemon Gold/Silver')
print()

trigger = True
# Prompts player 1 to choose a Pokemon to battle with
while trigger:
	player_1_pokemon_string = input(f'{player_1_name}, please select a Pokemon from the list by inputing the name of the Pokemon!: ')

	if player_1_pokemon_string.lower() in pokemon_list:
		player_1_pokemon = poke_fac.make(player_1_pokemon_string, player = (1, player_1_name)) #Creates a new object for player 1's Pokemon and assign it to Player 1
		print (f'{player_1_name}, you have chosen {player_1_pokemon.name}!')
		print()
		trigger = False

	elif player_1_pokemon_string.lower() == 'magikarp':
		print_magikarp()

	else:
		print('Invalid input!')
		print() 

trigger = True
# Prompts player 2 to choose a Pokemon to battle with
while trigger:
	player_2_pokemon_string = input(f'{player_2_name}, please select a Pokemon from the list by inputing the name of the Pokemon!: ')

	if player_2_pokemon_string.lower() in pokemon_list:
		player_2_pokemon = poke_fac.make(player_2_pokemon_string, player = (2, player_2_name)) #Creates a new object for player 2's Pokemon and assign it to Player 2
		print (f'{player_2_name}, you have chosen {player_2_pokemon.name}!')
		print()
		trigger = False

	elif player_2_pokemon_string.lower() in pokemon_list:
		print_magikarp()

	else:
		print('Invalid input!')
		print()

# Assigns the opponent Pokemon to each of the player
player_1_pokemon.bind_opp(player_2_pokemon)
player_2_pokemon.bind_opp(player_1_pokemon)

# The battle begins
print('_________________________________________________________________')
print('Let the battle begin!')
print(f'{player_1_name} - {player_1_pokemon.name} VS. {player_2_name} - {player_2_pokemon.name}!')
print('_________________________________________________________________')
print()

trigger = True # So that the game can run infinitely, until trigger = False, when one of the Pokemon's HP decreases to 0.

while trigger:
	display_hp_status()
	player_1_move = player_1_pokemon.select_move() # Prompts the player to select a move
	print()
	player_2_move = player_2_pokemon.select_move()
	print()

	# Speed comparison and move priority comparison to determine which Pokemon will move first
	if player_1_move.priority > player_2_move.priority:
		# The Pokemon make their moves
		print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
		print()

		if 'freeze' in player_1_pokemon.status:
			print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")

		player_1_pokemon.move()
		print()
		display_hp_status()
		
		if check_0_hp(player_2_pokemon) == True:
			trigger = False
			break

		print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
		print()

		if 'freeze' in player_2_pokemon.status:
			print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")

		player_2_pokemon.move()
		print()

		if check_0_hp(player_1_pokemon) == True:
			trigger = False
			break

		if player_2_pokemon.speed > player_1_pokemon.speed:
			# The Pokemon receive any status effects
			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break

			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break

		else:
			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break
			
			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break

	elif player_2_move.priority > player_1_move.priority:
		print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
		print()

		if 'freeze' in player_2_pokemon.status:
			print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")

		player_2_pokemon.move()
		print()
		display_hp_status()

		if check_0_hp(player_1_pokemon) == True:
			trigger = False
			break
		
		print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
		print()

		if 'freeze' in player_1_pokemon.status:
			print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")

		player_1_pokemon.move()
		print()

		if check_0_hp(player_2_pokemon) == True:
			trigger = False
			break

		if player_2_pokemon.speed > player_1_pokemon.speed:
			# The Pokemon receive any status effects
			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break

			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break

		else:
			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break

			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break

	elif player_1_move.priority == player_2_move.priority:
		if player_1_pokemon.speed > player_2_pokemon.speed:
			print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
			print()

			if 'freeze' in player_1_pokemon.status:
				print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")

			player_1_pokemon.move()
			print()
			display_hp_status()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break
			
			print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
			print()

			if 'freeze' in player_2_pokemon.status:
				print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")
					
			player_2_pokemon.move()
			print()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break
			
			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break
			
			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break

		elif player_2_pokemon.speed > player_1_pokemon.speed:
			print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
			print()

			if 'freeze' in player_2_pokemon.status:
				print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")
					
			player_2_pokemon.move()
			print()
			display_hp_status()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break
			
			print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
			print()

			if 'freeze' in player_1_pokemon.status:
				print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")
					
			player_1_pokemon.move()
			print()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break
			
			player_2_pokemon.status_effect()

			if check_0_hp(player_2_pokemon) == True:
				trigger = False
				break
			
			player_1_pokemon.status_effect()

			if check_0_hp(player_1_pokemon) == True:
				trigger = False
				break

		elif player_1_pokemon.speed == player_2_pokemon.speed:
			random_number = random.random() < 0.5

			if random_number < 0.5:
				print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
				print()

				if 'freeze' in player_1_pokemon.status:
					print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")

				player_1_pokemon.move()
				print()
				display_hp_status()

				if check_0_hp(player_2_pokemon) == True:
					trigger = False
					break
				
				print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
				print()

				if 'freeze' in player_2_pokemon.status:
					print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")
					
				player_2_pokemon.move()
				print()

				if check_0_hp(player_1_pokemon) == True:
					trigger = False
					break
				
				player_1_pokemon.status_effect()

				if check_0_hp(player_1_pokemon) == True:
					trigger = False
					break
				
				player_2_pokemon.status_effect()

				if check_0_hp(player_2_pokemon) == True:
					trigger = False
					break

			else:
				print(f"{player_2_name}'s {player_2_pokemon.name} used {player_2_move.name}!")
				print()

				if 'freeze' in player_2_pokemon.status:
					print(f"{player_2_name}'s {player_2_pokemon.name} can't move as it is frozen!")
					
				player_2_pokemon.move()
				print()
				display_hp_status()

				if check_0_hp(player_1_pokemon) == True:
					trigger = False
					break
				
				print(f"{player_1_name}'s {player_1_pokemon.name} used {player_1_move.name}!")
				print()

				if 'freeze' in player_1_pokemon.status:
					print(f"{player_1_name}'s {player_1_pokemon.name} can't move as it is frozen!")
					
				player_1_pokemon.move()
				print()

				if check_0_hp(player_2_pokemon) == True:
					trigger = False
					break
				
				player_2_pokemon.status_effect()

				if check_0_hp(player_2_pokemon) == True:
					trigger = False
					break
				
				player_1_pokemon.status_effect()

				if check_0_hp(player_1_pokemon) == True:
					trigger = False
					break

# End of game
# The following "Game Over" ASCII art is from https://textart4u.blogspot.com/2013/05/game-over-text-art.html
print('''
███▀▀▀██┼███▀▀▀███┼███▀█▄█▀███┼██▀▀▀
██┼┼┼┼██┼██┼┼┼┼┼██┼██┼┼┼█┼┼┼██┼██┼┼┼
██┼┼┼▄▄▄┼██▄▄▄▄▄██┼██┼┼┼▀┼┼┼██┼██▀▀▀
██┼┼┼┼██┼██┼┼┼┼┼██┼██┼┼┼┼┼┼┼██┼██┼┼┼
███▄▄▄██┼██┼┼┼┼┼██┼██┼┼┼┼┼┼┼██┼██▄▄▄
┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼┼
███▀▀▀███┼▀███┼┼██▀┼██▀▀▀┼██▀▀▀▀██▄┼
██┼┼┼┼┼██┼┼┼██┼┼██┼┼██┼┼┼┼██┼┼┼┼┼██┼
██┼┼┼┼┼██┼┼┼██┼┼██┼┼██▀▀▀┼██▄▄▄▄▄▀▀┼
██┼┼┼┼┼██┼┼┼██┼┼█▀┼┼██┼┼┼┼██┼┼┼┼┼██┼
███▄▄▄███┼┼┼─▀█▀┼┼─┼██▄▄▄┼██┼┼┼┼┼██▄
''')
print()
print('Thank you for playing this game!')