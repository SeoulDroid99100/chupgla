# test.py
import importlib
import unittest
import asyncio
from shivu.modules.lpvp.utils import create_pokemon, assign_pokemon, get_user_pokemon, get_active_pokemon, set_active_pokemon
from shivu.modules.lpvp.pokemon import Pokemon
from shivu.modules.lpvp.move import Move
from shivu import xy  # Import the database connection
from unittest.mock import patch, AsyncMock  # Import mocking tools

# Mock the MongoDB database interactions for testing purposes.
# Replace with your actual test database if you want integrated tests.


class MockAsyncIOMotorCollection:
    def __init__(self):
        self.data = {}

    async def find_one(self, query, *args, **kwargs):
        user_id = query.get("user_id")
        if user_id and user_id in self.data:
            return self.data[user_id]
        return None
    
    async def find_one_and_update(self, *args, **kwargs):
        #This simplify update, for test purposes.
        pass

    async def update_one(self, query, update, *args, **kwargs):
        user_id = query.get("user_id")
        upsert = kwargs.get("upsert", False)

        if user_id is None:
          return  # or raise an appropriate exception

        if user_id in self.data:
            #Simulate $set
            if "$set" in update:
                for key, value in update["$set"].items():
                    # Handle nested keys (like "pokemon.team")
                    keys = key.split(".")
                    current = self.data[user_id]
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value
            #Simulate $inc
            if '$inc' in update:
              for key, val in update['$inc'].items():
                keys = key.split('.')
                d = self.data[user_id]
                for k in keys[:-1]:
                  d = d.setdefault(k, {})
                d[keys[-1]] = d.get(keys[-1], 0) + val
            #Simulate $push
            if '$push' in update:
              for key, val in update['$push'].items():
                keys = key.split('.')
                d = self.data[user_id]
                for k in keys[:-1]:
                  d = d.setdefault(k, {})
                if keys[-1] not in d:
                    d[keys[-1]] = []  # Initialize as a list if it doesn't exist
                d[keys[-1]].append(val) #append the values.
        elif upsert:
            self.data[user_id] = update.get("$set", {})  # Initialize with $set values, if available

    async def insert_one(self, document, *args, **kwargs):
      user_id = document.get('user_id')
      if user_id is not None:
        self.data[user_id] = document
      else:
        print("Error inserting document: Missing 'user_id'")

    async def distinct(self, key, *args, **kwargs):
        return list(self.data.keys())


class TestLpvpUtils(unittest.IsolatedAsyncioTestCase):  # Use IsolatedAsyncioTestCase

    async def asyncSetUp(self):
        """Setup before each test."""
        # Mock the database connection.
        self.mock_db = MockAsyncIOMotorCollection()
        self.patcher = patch('shivu.xy', new=self.mock_db)  # Correct way to patch
        self.patcher.start()

    async def asyncTearDown(self):
      """Tear down after each test"""
      self.patcher.stop()

    async def test_create_pokemon(self):
        """Test Pokemon creation."""
        pokemon = create_pokemon("Pikachu", 123)  # Assuming Pikachu exists
        self.assertIsInstance(pokemon, Pokemon, "create_pokemon should return a Pokemon instance.")
        self.assertEqual(pokemon.player, (123, "Player"), "Player ID should be set correctly.")
        self.assertEqual(pokemon.name, "Pikachu", "Pokemon name should be set correctly.")
        self.assertTrue(len(pokemon._moves) > 0, "Pokemon should have moves.")
        for move in pokemon._moves:
            self.assertIsInstance(move, Move, "Each move should be a Move instance.")
            self.assertEqual(move.pp, move.max_pp) # Check pp and max_pp
            self.assertIsNotNone(move.name, "Move should have name")


        # Test invalid Pokemon
        invalid_pokemon = create_pokemon("InvalidPokemon", 456)
        self.assertIsNone(invalid_pokemon, "create_pokemon should return None for invalid Pokémon.")

    async def test_assign_pokemon(self):
        """Test assigning Pokémon to a user."""
        user_id = 123
        pokemon_list = await assign_pokemon(user_id)
        self.assertEqual(len(pokemon_list), 6, "assign_pokemon should assign 6 Pokémon.")
        for pokemon in pokemon_list:
            self.assertIsInstance(pokemon, Pokemon, "Each assigned Pokémon should be a Pokemon instance.")

        # Check that data was "written" to the mocked database.
        user_data = await self.mock_db.find_one({"user_id": user_id})
        self.assertIsNotNone(user_data, "User data should be saved to the database.")
        self.assertIn("pokemon", user_data, "User data should have a 'pokemon' field.")
        self.assertIn("team", user_data["pokemon"], "User data should have a 'pokemon.team' field.")
        self.assertEqual(len(user_data["pokemon"]["team"]), 6, "The 'pokemon.team' field should have 6 Pokémon names.")

    async def test_get_user_pokemon(self):
        """Test retrieving a user's Pokémon team."""
         # First, assign some Pokemon to the user.
        user_id = 456
        await assign_pokemon(user_id)
        pokemon_team = await get_user_pokemon(user_id)
        self.assertEqual(len(pokemon_team), 6, "get_user_pokemon should return 6 Pokémon.")
        for pokemon in pokemon_team:
          self.assertIsInstance(pokemon, Pokemon, "check instance")

         # Test with a user that doesn't exist
        non_existent_user_team = await get_user_pokemon(999)
        self.assertEqual(len(non_existent_user_team), 0, "get_user_pokemon should return an empty list for non-existent users.")

    async def test_get_and_set_active_pokemon(self):
      """Test getting and setting the active Pokemon"""
      user_id = 789
      await assign_pokemon(user_id) #Ensure user has pokemon
      
      #Get initial Active pokemon
      initial_active = await get_active_pokemon(user_id)
      self.assertIsNotNone(initial_active, "get active not working")

      #Set a *new* active Pokemon (index 2)
      await set_active_pokemon(user_id, 2)
      new_active = await get_active_pokemon(user_id)
      user_data = await self.mock_db.find_one({'user_id': user_id}) #Get updated data
      self.assertEqual(user_data['pokemon']['active'], 2, "Active pokemon index has been set.")
      self.assertNotEqual(initial_active.name, new_active.name, "Active Pokemon did change")


    async def test_invalid_move_creation(self):
      """ Test handling missing moves, and error logs"""
      with self.assertLogs() as cm:
        pokemon = create_pokemon("Blastoise", 111) #Move not in database
        self.assertIn("ERROR:root:Move 'InvalidMove' not found for Blastoise.", cm.output[0])

    async def test_pokemon_no_moves(self):
      """ Test handling pokemon without moves"""
      pokemon = create_pokemon("Charizard", 121) # Charizard does not have a list of moves
      self.assertIsNotNone(pokemon._moves, "Should exist a list of moves")

    async def test_stat_calculation(self):
      """Test pokemon stats"""
      poke = create_pokemon("Snorlax", 123)
      self.assertGreater(poke.hp, 0, "HP should be greater than zero after calculation.")
      self.assertGreater(poke.attack, 0, "Attack should be greater 0.")
      
      #Test stages
      original_attack = poke.attack
      poke.stages.attack += 1 #Increase attack
      self.assertGreater(poke.attack, original_attack)
      poke.stages.attack -= 2
      self.assertLess(poke.attack, original_attack)

    async def test_move_pp(self):
      """Test pp."""
      poke = create_pokemon("Snorlax", 123)
      self.assertGreater(len(poke._moves), 0, "Moves should exist")
      move = poke._moves[0] #Get a move
      original_pp = move.pp
      move.apply_move(poke) # Dummy Apply, target itself.
      self.assertEqual(move.pp, original_pp-1, "pp should decrease")

    async def test_status_effect(self):
       """Test status effects"""
       poke1 = create_pokemon("Snorlax", 123)
       poke2 = create_pokemon("Snorlax", 456)

       #Bind
       poke1.bind_opp(poke2)
       poke2.bind_opp(poke1)

       poke1.add_status('burn')
       self.assertIn('burn', poke1.status)
       original_hp = poke1.hp
       poke1.status_effect() # Call for effect
       self.assertLess(poke1.hp, original_hp, "HP should decrease due to burn")
       poke1.remove_status('burn')
       self.assertNotIn('burn', poke1.status)
       
       # Test Flinch
       poke1.add_status('flinch')
       self.assertIn('flinch', poke1.status)
       poke1.status_effect()  # Apply status effect
       self.assertNotIn('flinch', poke1.status)  # Flinch should be removed after one turn

       # Test Sleep
       poke1.add_status('sleep')
       self.assertIn('sleep', poke1.status)
       turns_slept = 0
       while 'sleep' in poke1.status:
         poke1.status_effect()
         turns_slept +=1
       self.assertGreaterEqual(turns_slept, 1)  # Check sleep lasted 1-3
       self.assertLessEqual(turns_slept, 3)

       # Test Paralysis
       poke1.add_status('paralyse')
       self.assertIn('paralyse', poke1.status)
       original_speed = poke1.speed
       poke1.status_effect() # Check speed reduction
       self.assertLess(poke1.speed, original_speed)
       poke1.remove_status('paralyse')
       self.assertEqual(poke1.speed, 2*original_speed)

       # Test Freeze
       poke1.add_status('freeze')
       self.assertIn('freeze', poke1.status)
       poke1.status_effect()

       # Test Bad Poison
       poke2.add_status('bad_poison')
       self.assertIn('bad_poison', poke2.status)
       original_hp = poke2.hp
       poke2.status_effect() # Check increasing damage.
       self.assertLess(poke2.hp, original_hp)

       # Test Leech Seed
       poke2.hp = poke2.max_hp #Restore health
       poke1.hp = poke1.max_hp
       original_hp_poke1 = poke1.hp
       original_hp_poke2 = poke2.hp
       poke2.add_status('leech_seed')
       poke2.status_effect() # Check effects
       self.assertGreater(poke1.hp, original_hp_poke1)
       self.assertLess(poke2.hp, original_hp_poke2)


if __name__ == '__main__':
    unittest.main()
