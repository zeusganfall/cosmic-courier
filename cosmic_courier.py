import sys
import json
import random
import os

class GameState:
    """Manages the overall state of the game."""
    def __init__(self, player, planets, game_data):
        self.player = player
        self.planets = planets
        self.game_data = game_data
        self.active_events = []

class Good:
    """Represents a good that can be traded."""
    def __init__(self, name, good_type, base_price, base_stock):
        self.name = name
        self.type = good_type
        self.base_price = base_price
        self.base_stock = base_stock

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Good):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

class Planet:
    """Represents a planet with a market."""
    def __init__(self, name, tech_level):
        self.name = name
        self.tech_level = tech_level
        self.market = None # To be replaced by a Market object

    def __repr__(self):
        return self.name

class Market:
    """Manages the market on a planet."""
    def __init__(self, planet, all_goods, modifiers, travel_options):
        self.planet = planet
        self.all_goods = all_goods
        self.modifiers = modifiers
        self.travel_options = travel_options
        self.prices = {}
        self.stock = {}
        self.fuel_price = 0

    def generate_market_data(self, active_events):
        """Generates dynamic prices and stock for all goods, and fuel price, considering active events."""
        self.prices = {}
        self.stock = {}
        for good in self.all_goods:
            price_modifier = self.modifiers[self.planet.tech_level][good.type]

            # Check for event effects
            for event in active_events:
                for effect in event["effects"]:
                    if effect["type"] == "price_modifier" and effect["good_type"] == good.type:
                        price_modifier *= effect["multiplier"]

            # Calculate price
            price_random_factor = random.uniform(0.9, 1.1)
            price = int(good.base_price * price_modifier * price_random_factor)
            self.prices[good] = price

            # Calculate stock (inversely related to price modifier)
            stock_modifier = 1 / price_modifier if price_modifier != 0 else 100
            stock_random_factor = random.uniform(0.8, 1.2)
            stock = int(good.base_stock * stock_modifier * stock_random_factor)
            self.stock[good] = max(0, stock)

        # Calculate fuel price
        fuel_price_modifier = self.modifiers[self.planet.tech_level]["fuel"]
        fuel_price_random_factor = random.uniform(0.95, 1.05)
        self.fuel_price = int(self.travel_options["base_fuel_price"] * fuel_price_modifier * fuel_price_random_factor)

class Ship:
    """Represents the player's ship."""
    def __init__(self, fuel_capacity=100, cargo_hold_size=50):
        self.fuel = fuel_capacity
        self.fuel_capacity = fuel_capacity
        self.cargo = {}  # {Good: quantity}
        self.cargo_hold_size = cargo_hold_size

    def get_cargo_count(self):
        """Returns the total number of items in the cargo hold."""
        return sum(self.cargo.values())

    def add_cargo(self, good, quantity):
        """Adds a quantity of a good to the cargo hold."""
        if self.get_cargo_count() + quantity > self.cargo_hold_size:
            return False
        self.cargo[good] = self.cargo.get(good, 0) + quantity
        return True

    def remove_cargo(self, good, quantity):
        """Removes a quantity of a good from the cargo hold."""
        if good not in self.cargo or self.cargo[good] < quantity:
            return False
        self.cargo[good] -= quantity
        if self.cargo[good] == 0:
            del self.cargo[good]
        return True


class Player:
    """Represents the player."""
    def __init__(self, name, ship, starting_planet, credits=1000):
        self.name = name
        self.ship = ship
        self.location = starting_planet
        self.credits = credits
        self.display_mode = "normal"  # "normal" or "compact"

def display_ui(game_state, last_action_message="Welcome to Cosmic Courier!", show_market=True):
    """Clears the screen and displays the game's UI."""
    player = game_state.player
    # 1. Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    # 2. Print Header
    print("🚀 Cosmic Courier")
    print("=============================")

    # 3. Print Status Panel
    cargo_status = f"{player.ship.get_cargo_count()} / {player.ship.cargo_hold_size}"
    cargo_str = ", ".join([f"{good.name} ({quantity})" for good, quantity in player.ship.cargo.items()]) or "Empty"
    print(f"🌍 Location: {player.location.name}")
    print(f"💳 Credits: {player.credits}")
    print(f"⛽ Fuel: {player.ship.fuel} / {player.ship.fuel_capacity}")
    print(f"📦 Cargo ({cargo_status}): {cargo_str}")
    print("-----------------------------")

    # 4. Print Last Action
    print("📝 Last Action:")
    print(last_action_message)
    print("-----------------------------")

    # 4.5. Print Active Events
    if game_state.active_events:
        print("📰 Galactic News:")
        for event in game_state.active_events:
            print(f"- {event['name']} (Turns remaining: {event['duration']})")
        print("-----------------------------")

    # 5. Print Market Panel (conditionally)
    if show_market:
        print(f"📊 Market on {player.location.name}:")
        if not player.location.market.prices:
            print("Market data is currently unavailable.")
        else:
            for good, price in player.location.market.prices.items():
                stock = player.location.market.stock.get(good, 0)
                print(f"- {good.name}: {price} credits (Stock: {stock})")
            print(f"- Fuel: {player.location.market.fuel_price} credits/unit")
        print("-----------------------------")

    # 6. Print Command Menu
    print("🔹 Available Commands:")
    print("[1] Travel to another planet")
    print("[2] Buy goods")
    print("[3] Sell goods")
    print("[4] Refuel ship")
    print("[5] Check status")
    print(f"[6] Toggle Display (Current: {player.display_mode.capitalize()})")
    print("[7] Quit game")
    print("=============================")

def setup_game(data_file="game_data.json"):
    """Sets up the initial game state from a data file."""
    with open(data_file, 'r') as f:
        game_data = json.load(f)

    # Create goods
    all_goods = [Good(g["name"], g["type"], g["base_price"], g["base_stock"]) for g in game_data["goods"]]

    # Get modifiers
    modifiers = game_data["tech_level_modifiers"]

    # Create planets and markets
    planets = []
    travel_options = game_data["travel_options"]
    for planet_data in game_data["planets"]:
        planet = Planet(planet_data["name"], planet_data["tech_level"])
        planet.market = Market(planet, all_goods, modifiers, travel_options)
        planets.append(planet)

    # Create ship and player
    ship_defaults = game_data["defaults"]["ship"]
    player_defaults = game_data["defaults"]["player"]

    ship = Ship(
        fuel_capacity=ship_defaults["fuel_capacity"],
        cargo_hold_size=ship_defaults["cargo_hold_size"]
    )

    starting_planet_name = player_defaults["starting_planet"]
    starting_planet = next((p for p in planets if p.name == starting_planet_name), None)
    if not starting_planet:
        raise ValueError(f"Starting planet '{starting_planet_name}' not found in planets list.")

    player = Player(
        "Captain",
        ship,
        starting_planet,
        credits=player_defaults["credits"]
    )

    # Create the game state
    game_state = GameState(player, planets, game_data)

    # Generate initial market data for the starting planet
    starting_planet.market.generate_market_data(game_state.active_events)

    return game_state

def handle_events(game_state):
    """Manages the lifecycle of galactic events."""
    player = game_state.player
    messages = []

    # Decrement duration of active events and remove expired ones
    for event in game_state.active_events[:]:
        event["duration"] -= 1
        if event["duration"] <= 0:
            messages.append(f"The '{event['name']}' event has ended.")
            game_state.active_events.remove(event)

    # Trigger new events
    event_chance = game_state.game_data["travel_options"]["event_trigger_chance"]
    if random.random() < event_chance:
        new_event = random.choice(game_state.game_data["events"])
        # Avoid duplicate events
        if not any(e['name'] == new_event['name'] for e in game_state.active_events):
            # The event data from JSON is a template, create a copy to modify
            active_event = new_event.copy()
            game_state.active_events.append(active_event)
            messages.append(f"A new galactic event has begun: {active_event['name']}!")
            messages.append(f"  > {active_event['description']}")

    return "\n".join(messages)

def game_loop(game_state):
    """The main game loop."""
    last_action_message = "Welcome to Cosmic Courier! What are your orders, Captain?"
    while True:
        player = game_state.player

        # Handle event lifecycle
        event_messages = handle_events(game_state)

        # Combine messages
        display_message = last_action_message
        if event_messages:
            display_message += "\n\n" + event_messages

        # Check for game over condition
        if player.ship.fuel <= 0 and player.credits <= 0:
            display_ui(game_state, "You've run out of fuel and credits!\nYour journey ends here.", show_market=False)
            print("\n--- GAME OVER ---")
            sys.exit()

        show_market = player.display_mode == 'normal'
        display_ui(game_state, display_message, show_market=show_market)

        try:
            choice = input("Enter command number: ")
            if not choice:
                last_action_message = "No command entered. Please try again."
                continue

            choice = int(choice)

            if choice == 1:
                last_action_message = travel(game_state)
            elif choice == 2:
                last_action_message = buy_goods(game_state)
            elif choice == 3:
                last_action_message = sell_goods(game_state)
            elif choice == 4:
                last_action_message = refuel_ship(game_state)
            elif choice == 5:
                last_action_message = "Status panel refreshed."
            elif choice == 6:
                if player.display_mode == "normal":
                    player.display_mode = "compact"
                else:
                    player.display_mode = "normal"
                last_action_message = f"Display mode switched to {player.display_mode.capitalize()}."
            elif choice == 7:
                print("Thank you for playing Cosmic Courier!")
                sys.exit()
            else:
                last_action_message = f"Invalid command number: {choice}"
        except ValueError:
            last_action_message = f"Invalid input. Please enter a number."

def travel(game_state):
    """Handles player travel between planets, with distance-based fuel and random events."""
    player = game_state.player
    planets = game_state.planets
    game_data = game_state.game_data
    destinations = [p for p in planets if p != player.location]

    message = "Please choose a destination."
    display_ui(game_state, message, show_market=False)
    print("\nAvailable destinations:")
    for i, planet in enumerate(destinations):
        distance = game_data["distance_matrix"][player.location.name][planet.name]
        print(f"{i + 1}. {planet.name} (Distance: {distance})")
    print(f"{len(destinations) + 1}. Cancel")

    try:
        choice = int(input("Choose a destination (number): ")) - 1

        if choice == len(destinations): # Cancel option
            return "Travel cancelled."

        if 0 <= choice < len(destinations):
            destination = destinations[choice]
            distance = game_data["distance_matrix"][player.location.name][destination.name]
            fuel_cost = distance * game_data["travel_options"]["base_fuel_cost_per_unit"]

            if player.ship.fuel >= fuel_cost:
                player.ship.fuel -= fuel_cost
                player.location = destination
                destination.market.generate_market_data(game_state.active_events)

                # Random event check
                event_chance = game_data["travel_options"]["random_event_chance"]
                # Check for event effects on travel risk
                for event in game_state.active_events:
                    for effect in event["effects"]:
                        if effect["type"] == "travel_risk_modifier":
                            event_chance *= effect["multiplier"]

                message = f"Traveled to {destination.name}. Fuel consumed: {fuel_cost}."

                if random.random() < event_chance:
                    event = random.choice(game_data["random_events"])
                    if event["effect"]["type"] == "fuel_loss":
                        fuel_loss = random.randint(event["effect"]["amount"][0], event["effect"]["amount"][1])
                        player.ship.fuel -= fuel_loss
                        message += f"\n{event['description']} Fuel -{fuel_loss}."

                return message
            else:
                return f"Not enough fuel. You need {fuel_cost} fuel, but you only have {player.ship.fuel}."
        else:
            return "Invalid destination choice."
    except (ValueError, IndexError):
        return "Invalid destination choice."

def buy_goods(game_state):
    """Handles buying multiple goods from a planet's market."""
    player = game_state.player
    display_ui(game_state, "What would you like to buy? (Type 'cancel' to exit)", show_market=True)
    good_name = input("Enter good name: ").lower()

    if good_name == 'cancel':
        return "Purchase cancelled."

    found_good = None
    for good in player.location.market.prices:
        if good.name.lower() == good_name:
            found_good = good
            break

    if not found_good:
        return f"'{good_name.capitalize()}' not found in this market."

    price = player.location.market.prices[found_good]
    stock = player.location.market.stock[found_good]

    if stock == 0:
        return f"{found_good.name} is out of stock."

    try:
        quantity = int(input(f"Enter quantity to buy (max {stock}, you have {player.credits} credits): "))
        if quantity <= 0:
            return "Quantity must be a positive number."
    except ValueError:
        return "Invalid quantity. Please enter a number."

    total_cost = price * quantity
    if quantity > stock:
        return f"Not enough stock. Only {stock} units available."
    if total_cost > player.credits:
        return f"Not enough credits. You need {total_cost} credits, but you only have {player.credits}."

    cargo_space_needed = quantity
    current_cargo_count = player.ship.get_cargo_count()
    if current_cargo_count + cargo_space_needed > player.ship.cargo_hold_size:
        return f"Not enough cargo space. You need {cargo_space_needed} units of space, but you only have {player.ship.cargo_hold_size - current_cargo_count} left."

    # Perform transaction
    player.credits -= total_cost
    player.ship.add_cargo(found_good, quantity)
    player.location.market.stock[found_good] -= quantity

    return f"Bought {quantity} unit(s) of {found_good.name} for {total_cost} credits."

def refuel_ship(game_state):
    """Handles refueling the player's ship."""
    player = game_state.player
    fuel_price = player.location.market.fuel_price
    needed_fuel = player.ship.fuel_capacity - player.ship.fuel

    if needed_fuel == 0:
        return "Fuel tank is already full."

    message = f"Fuel costs {fuel_price} credits per unit. Your tank has space for {needed_fuel} units."
    display_ui(game_state, message, show_market=False)

    try:
        quantity = int(input(f"Enter amount to refuel (max {needed_fuel}): "))
        if quantity <= 0:
            return "Amount must be a positive number."
    except ValueError:
        return "Invalid amount. Please enter a number."

    if quantity > needed_fuel:
        return f"Your tank can only hold {needed_fuel} more units of fuel."

    total_cost = fuel_price * quantity
    if total_cost > player.credits:
        return f"Not enough credits. You need {total_cost} credits, but you only have {player.credits}."

    # Perform transaction
    player.credits -= total_cost
    player.ship.fuel += quantity

    return f"Refueled {quantity} units for {total_cost} credits. Fuel is now {player.ship.fuel}/{player.ship.fuel_capacity}."

def sell_goods(game_state):
    """Handles selling multiple goods from the player's cargo."""
    player = game_state.player
    display_ui(game_state, "What would you like to sell? (Type 'cancel' to exit)", show_market=True)
    good_name = input("Enter good name: ").lower()

    if good_name == 'cancel':
        return "Sale cancelled."

    good_to_sell = None
    for good in player.ship.cargo:
        if good.name.lower() == good_name:
            good_to_sell = good
            break

    if not good_to_sell:
        return f"'{good_name.capitalize()}' not found in your cargo."

    price = player.location.market.prices.get(good_to_sell)
    if price is None:
        return f"This planet does not buy {good_to_sell.name}."

    current_quantity = player.ship.cargo[good_to_sell]

    try:
        quantity_to_sell = int(input(f"Enter quantity to sell (you have {current_quantity}): "))
        if quantity_to_sell <= 0:
            return "Quantity must be a positive number."
    except ValueError:
        return "Invalid quantity. Please enter a number."

    if quantity_to_sell > current_quantity:
        return f"You don't have enough. You only have {current_quantity} units of {good_to_sell.name}."

    # Perform transaction
    total_sale = price * quantity_to_sell
    player.credits += total_sale
    player.ship.remove_cargo(good_to_sell, quantity_to_sell)
    player.location.market.stock[good_to_sell] += quantity_to_sell # Add sold goods back to market

    return f"Sold {quantity_to_sell} unit(s) of {good_to_sell.name} for {total_sale} credits."

if __name__ == "__main__":
    game_state = setup_game()
    game_loop(game_state)
