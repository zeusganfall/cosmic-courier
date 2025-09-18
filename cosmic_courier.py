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

class Mission:
    """Represents a delivery mission."""
    def __init__(self, origin, destination, good, quantity, reward, faction):
        self.origin = origin
        self.destination = destination
        self.good = good
        self.quantity = quantity
        self.reward = reward
        self.faction = faction

    def __str__(self):
        return f"Deliver {self.quantity} {self.good.name} from {self.origin.name} to {self.destination.name} for {self.reward} credits."

class Planet:
    """Represents a planet with a market."""
    def __init__(self, name, tech_level, faction):
        self.name = name
        self.tech_level = tech_level
        self.faction = faction
        self.market = None
        self.mission_board = []

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
        self.prices = {}
        self.stock = {}
        for good in self.all_goods:
            price_modifier = self.modifiers[self.planet.tech_level][good.type]

            for event in active_events:
                for effect in event["effects"]:
                    if effect["type"] == "price_modifier" and effect["good_type"] == good.type:
                        price_modifier *= effect["multiplier"]

            price_random_factor = random.uniform(0.9, 1.1)
            price = int(good.base_price * price_modifier * price_random_factor)
            self.prices[good] = price

            stock_modifier = 1 / price_modifier if price_modifier != 0 else 100
            stock_random_factor = random.uniform(0.8, 1.2)
            stock = int(good.base_stock * stock_modifier * stock_random_factor)
            self.stock[good] = max(0, stock)

        fuel_price_modifier = self.modifiers[self.planet.tech_level]["fuel"]
        fuel_price_random_factor = random.uniform(0.95, 1.05)
        self.fuel_price = int(self.travel_options["base_fuel_price"] * fuel_price_modifier * fuel_price_random_factor)

class Ship:
    """Represents the player's ship."""
    def __init__(self, upgrades_data):
        self.upgrades_data = upgrades_data
        self.cargo_hold_level = 1
        self.fuel_tank_level = 1
        self.engine_level = 1
        self.cargo = {}
        self._update_stats_from_levels()
        self.fuel = self.fuel_capacity

    def _update_stats_from_levels(self):
        cargo_data = self.upgrades_data["cargo_hold"][self.cargo_hold_level - 1]
        self.cargo_hold_size = cargo_data["size"]
        fuel_tank_data = self.upgrades_data["fuel_tank"][self.fuel_tank_level - 1]
        self.fuel_capacity = fuel_tank_data["capacity"]
        engine_data = self.upgrades_data["engine"][self.engine_level - 1]
        self.engine_efficiency = engine_data["efficiency"]

    def get_cargo_count(self):
        return sum(self.cargo.values())

    def add_cargo(self, good, quantity):
        if self.get_cargo_count() + quantity > self.cargo_hold_size:
            return False
        self.cargo[good] = self.cargo.get(good, 0) + quantity
        return True

    def remove_cargo(self, good, quantity):
        if good not in self.cargo or self.cargo[good] < quantity:
            return False
        self.cargo[good] -= quantity
        if self.cargo[good] == 0:
            del self.cargo[good]
        return True

class Player:
    """Represents the player."""
    def __init__(self, name, ship, starting_planet, credits=1000, factions=[]):
        self.name = name
        self.ship = ship
        self.location = starting_planet
        self.credits = credits
        self.display_mode = "normal"
        self.reputation = {faction: 0 for faction in factions}
        self.current_mission = None
        self.debt = 0

def display_ui(game_state, last_action_message="Welcome to Cosmic Courier!", show_market=True):
    player = game_state.player
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🚀 Cosmic Courier")
    print("=============================")
    cargo_status = f"{player.ship.get_cargo_count()} / {player.ship.cargo_hold_size}"
    cargo_str = ", ".join([f"{good.name} ({quantity})" for good, quantity in player.ship.cargo.items()]) or "Empty"
    print(f"🌍 Location: {player.location.name}")
    print(f"💳 Credits: {player.credits}")
    print(f"💰 Debt: {player.debt}")
    reputation_str = ", ".join([f"{faction}: {rep}" for faction, rep in player.reputation.items()])
    print(f"🤝 Reputation: {reputation_str}")
    print(f"⛽ Fuel: {player.ship.fuel} / {player.ship.fuel_capacity}")
    print(f"📦 Cargo ({cargo_status}): {cargo_str}")
    print("-----------------------------")
    if player.current_mission:
        print("🎯 Current Mission:")
        print(f"  {player.current_mission}")
        print("-----------------------------")
    print("📝 Last Action:")
    print(last_action_message)
    print("-----------------------------")
    if game_state.active_events:
        print("📰 Galactic News:")
        for event in game_state.active_events:
            print(f"- {event['name']} (Turns remaining: {event['duration']})")
        print("-----------------------------")
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

    print("🔹 Available Commands:")
    print("[1] Travel to another planet")
    print("[2] Buy goods")
    print("[3] Sell goods")
    print("[4] Refuel ship")
    print("[5] Visit shipyard")
    print("[6] View mission board")
    print("[7] Repay debt")
    print("[8] Check status")
    print(f"[9] Toggle Display (Current: {player.display_mode.capitalize()})")
    print("[10] Quit game")
    print("=============================")

def setup_game(data_file="game_data.json"):
    with open(data_file, 'r') as f:
        game_data = json.load(f)
    all_goods = {g['name']: Good(g["name"], g["type"], g["base_price"], g["base_stock"]) for g in game_data["goods"]}
    modifiers = game_data["tech_level_modifiers"]
    planets = []
    travel_options = game_data["travel_options"]
    for planet_data in game_data["planets"]:
        planet = Planet(planet_data["name"], planet_data["tech_level"], planet_data["faction"])
        planet.market = Market(planet, all_goods.values(), modifiers, travel_options)
        planets.append(planet)
    ship_upgrades_data = game_data["ship_upgrades"]
    ship = Ship(ship_upgrades_data)
    player_defaults = game_data["defaults"]["player"]
    starting_planet_name = player_defaults["starting_planet"]
    starting_planet = next((p for p in planets if p.name == starting_planet_name), None)
    if not starting_planet:
        raise ValueError(f"Starting planet '{starting_planet_name}' not found in planets list.")
    player = Player("Captain", ship, starting_planet, credits=player_defaults["credits"], factions=game_data["factions"])
    game_state = GameState(player, planets, game_data)
    starting_planet.market.generate_market_data(game_state.active_events)
    return game_state

def apply_interest(game_state):
    player = game_state.player
    if player.debt > 0:
        interest_rate = game_state.game_data["loan_system"]["interest_rate"]
        interest_amount = int(player.debt * interest_rate)
        player.debt += interest_amount
        return f"An interest charge of {interest_amount} credits has been added to your debt."
    return ""

def handle_events(game_state):
    messages = []
    for event in game_state.active_events[:]:
        event["duration"] -= 1
        if event["duration"] <= 0:
            messages.append(f"The '{event['name']}' event has ended.")
            game_state.active_events.remove(event)
    event_chance = game_state.game_data["travel_options"]["event_trigger_chance"]
    if random.random() < event_chance:
        new_event = random.choice(game_state.game_data["events"])
        if not any(e['name'] == new_event['name'] for e in game_state.active_events):
            active_event = new_event.copy()
            game_state.active_events.append(active_event)
            messages.append(f"A new galactic event has begun: {active_event['name']}!")
            messages.append(f"  > {active_event['description']}")
    return "\n".join(messages)

def complete_mission(game_state):
    player = game_state.player
    mission = player.current_mission
    player.credits += mission.reward
    player.reputation[mission.faction] += 1
    player.ship.remove_cargo(mission.good, mission.quantity)
    player.current_mission = None
    return f"Mission complete! Delivered {mission.quantity} {mission.good.name} to {mission.destination.name}.\nReward: {mission.reward} credits. Reputation with {mission.faction} increased."

def handle_game_end(message):
    """Handles the game end screen and prompts for restart or quit."""
    print(message)
    print("\n--- GAME OVER ---")
    while True:
        choice = input("Play again? (y/n): ").lower()
        if choice == 'y':
            return "restart"
        elif choice == 'n':
            return "quit"

def offer_loan(game_state):
    player = game_state.player
    loan_amount = game_state.game_data["loan_system"]["loan_amount"]
    message = f"You are stranded without fuel or credits. A mysterious benefactor offers you a loan of {loan_amount} credits. Accept? (y/n)"
    display_ui(game_state, message, show_market=False)
    choice = input("> ").lower()
    if choice == 'y':
        player.credits += loan_amount
        player.debt += loan_amount
        return f"You have accepted the loan. {loan_amount} credits have been added. Good luck."
    else:
        return "GAME OVER"

def game_loop(game_state):
    last_action_message = "Welcome to Cosmic Courier! What are your orders, Captain?"
    while True:
        player = game_state.player
        event_messages = handle_events(game_state)
        interest_message = apply_interest(game_state)
        if player.current_mission and player.location == player.current_mission.destination:
            if player.ship.cargo.get(player.current_mission.good, 0) >= player.current_mission.quantity:
                last_action_message = complete_mission(game_state)
        display_message = last_action_message
        if event_messages:
            display_message += "\n\n" + event_messages
        if interest_message:
            display_message += "\n" + interest_message

        # Win/Loss Condition Checks
        win_credits = game_state.game_data["game_goals"]["win_credits"]
        if player.credits >= win_credits and player.debt == 0:
            return handle_game_end(f"Congratulations! You've reached {win_credits} credits with no debt and won the game!")

        max_debt = game_state.game_data["game_goals"]["max_debt"]
        if player.debt > max_debt:
            return handle_game_end(f"You have exceeded the maximum debt of {max_debt}. The bank has seized your assets.")

        if player.ship.fuel <= 0 and player.credits <= 0 and player.ship.get_cargo_count() == 0:
            loan_result = offer_loan(game_state)
            if loan_result == "GAME OVER":
                return handle_game_end("You declined the loan and were left stranded. Your journey ends here.")
            else:
                last_action_message = loan_result

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
                last_action_message = visit_shipyard(game_state)
            elif choice == 6:
                last_action_message = view_mission_board(game_state)
            elif choice == 7:
                last_action_message = repay_debt(game_state)
            elif choice == 8:
                last_action_message = "Status panel refreshed."
            elif choice == 9:
                if player.display_mode == "normal":
                    player.display_mode = "compact"
                else:
                    player.display_mode = "normal"
                last_action_message = f"Display mode switched to {player.display_mode.capitalize()}."
            elif choice == 10:
                print("Thank you for playing Cosmic Courier!")
                sys.exit()
            else:
                last_action_message = f"Invalid command number: {choice}"
        except ValueError:
            last_action_message = f"Invalid input. Please enter a number."

def travel(game_state):
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
        if choice == len(destinations):
            return "Travel cancelled."
        if 0 <= choice < len(destinations):
            destination = destinations[choice]
            distance = game_data["distance_matrix"][player.location.name][destination.name]
            fuel_cost = int(distance * game_data["travel_options"]["base_fuel_cost_per_unit"] * player.ship.engine_efficiency)
            if player.ship.fuel >= fuel_cost:
                player.ship.fuel -= fuel_cost
                player.location = destination
                destination.market.generate_market_data(game_state.active_events)
                event_chance = game_data["travel_options"]["random_event_chance"]
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
    player = game_state.player
    market = player.location.market
    tradable_goods = [g for g in market.prices if market.stock.get(g, 0) > 0]
    if not tradable_goods:
        return "There are no goods available to buy at this market."
    message = "Please choose a good to buy."
    display_ui(game_state, message, show_market=True)
    print("\nAvailable goods to buy:")
    for i, good in enumerate(tradable_goods):
        price = market.prices[good]
        stock = market.stock[good]
        print(f"{i + 1}. {good.name} (Price: {price}, Stock: {stock})")
    print(f"{len(tradable_goods) + 1}. Cancel")
    try:
        choice_str = input("Choose a good to buy (number): ")
        if not choice_str:
            return "No selection made. Purchase cancelled."
        choice = int(choice_str) - 1
        if choice == len(tradable_goods):
            return "Purchase cancelled."
        if 0 <= choice < len(tradable_goods):
            found_good = tradable_goods[choice]
            price = market.prices[found_good]
            stock = market.stock[found_good]
            try:
                quantity_str = input(f"Enter quantity to buy (max {stock}, you have {player.credits} credits): ")
                if not quantity_str:
                    return "No quantity entered. Purchase cancelled."
                quantity = int(quantity_str)
                if quantity <= 0:
                    return "Quantity must be a positive number."
            except ValueError:
                return "Invalid quantity. Please enter a number."
            total_cost = price * quantity
            if quantity > stock:
                return f"Not enough stock. Only {stock} units available."
            if total_cost > player.credits:
                return f"Not enough credits. You need {total_cost} credits, but you only have {player.credits}."
            current_cargo_count = player.ship.get_cargo_count()
            if current_cargo_count + quantity > player.ship.cargo_hold_size:
                return f"Not enough cargo space. You need {quantity} units of space, but you only have {player.ship.cargo_hold_size - current_cargo_count} left."
            player.credits -= total_cost
            player.ship.add_cargo(found_good, quantity)
            market.stock[found_good] -= quantity
            return f"Bought {quantity} unit(s) of {found_good.name} for {total_cost} credits."
        else:
            return "Invalid choice."
    except (ValueError, IndexError):
        return "Invalid choice. Please enter a number."

def refuel_ship(game_state):
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
    player.credits -= total_cost
    player.ship.fuel += quantity
    return f"Refueled {quantity} units for {total_cost} credits. Fuel is now {player.ship.fuel}/{player.ship.fuel_capacity}."

def _attempt_upgrade(player, ship, component_name, level_attr, upgrade_key):
    current_level = getattr(ship, level_attr)
    max_level = len(ship.upgrades_data[upgrade_key])

    if current_level >= max_level:
        return f"{component_name} is already at max level."

    next_level_data = ship.upgrades_data[upgrade_key][current_level]
    cost = next_level_data['cost']

    if player.credits < cost:
        return f"Not enough credits for {component_name} upgrade."

    player.credits -= cost
    setattr(ship, level_attr, current_level + 1)
    ship._update_stats_from_levels()

    new_level = getattr(ship, level_attr)
    if component_name == "Cargo Hold":
        return f"Cargo Hold upgraded to Level {new_level}! New capacity: {ship.cargo_hold_size}."
    elif component_name == "Fuel Tank":
        return f"Fuel Tank upgraded to Level {new_level}! New capacity: {ship.fuel_capacity}."
    elif component_name == "Engine":
        return f"Engine upgraded to Level {new_level}! New efficiency: {ship.engine_efficiency}."
    return "Error in upgrade."

def visit_shipyard(game_state):
    player = game_state.player
    ship = player.ship
    upgrades = ship.upgrades_data
    while True:
        message = "Welcome to the shipyard! Select a component to upgrade.\n\n"
        cargo_level = ship.cargo_hold_level
        max_cargo_level = len(upgrades["cargo_hold"])
        message += f"[1] Cargo Hold (Level {cargo_level}/{max_cargo_level})\n"
        if cargo_level < max_cargo_level:
            next_level_data = upgrades["cargo_hold"][cargo_level]
            message += f"    Next Level: {next_level_data['size']} units. Cost: {next_level_data['cost']} credits.\n"
        else:
            message += "    Max level reached.\n"
        fuel_level = ship.fuel_tank_level
        max_fuel_level = len(upgrades["fuel_tank"])
        message += f"[2] Fuel Tank (Level {fuel_level}/{max_fuel_level})\n"
        if fuel_level < max_fuel_level:
            next_level_data = upgrades["fuel_tank"][fuel_level]
            message += f"    Next Level: {next_level_data['capacity']} capacity. Cost: {next_level_data['cost']} credits.\n"
        else:
            message += "    Max level reached.\n"
        engine_level = ship.engine_level
        max_engine_level = len(upgrades["engine"])
        message += f"[3] Engine (Level {engine_level}/{max_engine_level})\n"
        if engine_level < max_engine_level:
            next_level_data = upgrades["engine"][engine_level]
            message += f"    Next Level: {next_level_data['efficiency'] * 100:.0f}% efficiency. Cost: {next_level_data['cost']} credits.\n"
        else:
            message += "    Max level reached.\n"
        message += "\n[4] Exit Shipyard"
        display_ui(game_state, message, show_market=False)
        choice = input("Enter your choice: ")
        if choice == '1':
            return _attempt_upgrade(player, ship, "Cargo Hold", "cargo_hold_level", "cargo_hold")
        elif choice == '2':
            return _attempt_upgrade(player, ship, "Fuel Tank", "fuel_tank_level", "fuel_tank")
        elif choice == '3':
            return _attempt_upgrade(player, ship, "Engine", "engine_level", "engine")
        elif choice == '4':
            return "Exiting shipyard."
        else:
            return "Invalid choice. Please try again."

def view_mission_board(game_state):
    player = game_state.player
    planet = player.location
    if not planet.mission_board:
        num_missions_to_generate = 3
        for _ in range(num_missions_to_generate):
            template = random.choice(game_state.game_data["mission_templates"])
            all_goods_map = {g.name: g for g in planet.market.all_goods}
            possible_goods = [g for g in all_goods_map.values() if g.type in template["good_types"]]
            if not possible_goods:
                continue
            good = random.choice(possible_goods)
            possible_destinations = [p for p in game_state.planets if p != planet]
            if not possible_destinations:
                continue
            destination = random.choice(possible_destinations)
            quantity = random.randint(template["min_quantity"], template["max_quantity"])
            base_reward = good.base_price * quantity * template["reward_multiplier"]
            reward = int(base_reward * random.uniform(0.9, 1.1))
            mission = Mission(planet, destination, good, quantity, reward, destination.faction)
            planet.mission_board.append(mission)

    message = "Welcome to the Mission Board."
    if not planet.mission_board:
        message += "\nThere are no missions available at this time."
    display_ui(game_state, message, show_market=False)

    if player.current_mission:
        return "You already have an active mission."

    if not planet.mission_board:
        return "No missions available."

    print("\nAvailable Missions:")
    for i, mission in enumerate(planet.mission_board):
        print(f"[{i+1}] {mission}")
    print(f"[{len(planet.mission_board) + 1}] Exit")

    try:
        choice = int(input("Choose a mission to accept: ")) - 1
        if 0 <= choice < len(planet.mission_board):
            player.current_mission = planet.mission_board.pop(choice)
            return f"Mission accepted! {player.current_mission}"
        elif choice == len(planet.mission_board):
            return "Exiting mission board."
        else:
            return "Invalid choice."
    except ValueError:
        return "Invalid input."

def repay_debt(game_state):
    """Handles the player debt repayment UI and logic."""
    player = game_state.player
    if player.debt == 0:
        return "You have no debt to repay. Congratulations!"

    message = f"You have {player.debt} credits of outstanding debt."
    display_ui(game_state, message, show_market=False)

    try:
        amount = int(input(f"Enter amount to repay (you have {player.credits} credits): "))
        if amount <= 0:
            return "Amount must be a positive number."
    except ValueError:
        return "Invalid amount. Please enter a number."

    if amount > player.debt:
        amount = player.debt

    if amount > player.credits:
        return f"You only have {player.credits} credits. Cannot repay that amount."

    player.credits -= amount
    player.debt -= amount

    return f"You repaid {amount} credits of your debt. Remaining debt: {player.debt}."

def sell_goods(game_state):
    player = game_state.player
    market = player.location.market
    if not player.ship.cargo:
        return "You have no cargo to sell."
    sellable_goods = [g for g in player.ship.cargo if g in market.prices]
    if not sellable_goods:
        return "This market doesn't seem to be buying any of the goods you are carrying."
    message = "Please choose a good to sell."
    display_ui(game_state, message, show_market=True)
    print("\nAvailable goods to sell:")
    for i, good in enumerate(sellable_goods):
        price = market.prices[good]
        quantity = player.ship.cargo[good]
        print(f"{i + 1}. {good.name} (Price: {price}, You have: {quantity})")
    print(f"{len(sellable_goods) + 1}. Cancel")
    try:
        choice_str = input("Choose a good to sell (number): ")
        if not choice_str:
            return "No selection made. Sale cancelled."
        choice = int(choice_str) - 1
        if choice == len(sellable_goods):
            return "Sale cancelled."
        if 0 <= choice < len(sellable_goods):
            good_to_sell = sellable_goods[choice]
            price = market.prices[good_to_sell]
            current_quantity = player.ship.cargo[good_to_sell]
            try:
                quantity_str = input(f"Enter quantity to sell (you have {current_quantity}): ")
                if not quantity_str:
                    return "No quantity entered. Sale cancelled."
                quantity_to_sell = int(quantity_str)
                if quantity_to_sell <= 0:
                    return "Quantity must be a positive number."
            except ValueError:
                return "Invalid quantity. Please enter a number."
            if quantity_to_sell > current_quantity:
                return f"You don't have enough. You only have {current_quantity} units of {good_to_sell.name}."
            total_sale = price * quantity_to_sell
            player.credits += total_sale
            player.ship.remove_cargo(good_to_sell, quantity_to_sell)
            market.stock[good_to_sell] = market.stock.get(good_to_sell, 0) + quantity_to_sell
            return f"Sold {quantity_to_sell} unit(s) of {good_to_sell.name} for {total_sale} credits."
        else:
            return "Invalid choice."
    except (ValueError, IndexError):
        return "Invalid choice. Please enter a number."

if __name__ == "__main__":
    while True:
        game_state = setup_game()
        result = game_loop(game_state)
        if result == "quit":
            print("Thanks for playing!")
            break
