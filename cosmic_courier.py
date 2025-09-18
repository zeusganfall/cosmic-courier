import sys
import json

class Good:
    """Represents a good that can be traded."""
    def __init__(self, name):
        self.name = name

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
    def __init__(self, name):
        self.name = name
        self.market = {}

    def add_good(self, good, price):
        """Adds a good to the planet's market with a given price."""
        self.market[good] = price

    def __repr__(self):
        return self.name

class Ship:
    """Represents the player's ship."""
    def __init__(self, fuel_capacity=100, cargo_hold_size=50):
        self.fuel = fuel_capacity
        self.fuel_capacity = fuel_capacity
        self.cargo = []
        self.cargo_hold_size = cargo_hold_size

    def add_cargo(self, good):
        """Adds a good to the cargo hold if there is space."""
        if len(self.cargo) < self.cargo_hold_size:
            self.cargo.append(good)
            return True
        return False

    def remove_cargo(self, good_name):
        """Removes a good from the cargo hold by its name."""
        for good in self.cargo:
            if good.name.lower() == good_name.lower():
                self.cargo.remove(good)
                return good
        return None


class Player:
    """Represents the player."""
    def __init__(self, name, ship, starting_planet, credits=1000):
        self.name = name
        self.ship = ship
        self.location = starting_planet
        self.credits = credits

def setup_game(data_file="game_data.json"):
    """Sets up the initial game state from a data file."""
    with open(data_file, 'r') as f:
        game_data = json.load(f)

    # Create goods
    goods = {name: Good(name) for name in game_data["goods"]}

    # Create planets
    planets = []
    for planet_data in game_data["planets"]:
        planet = Planet(planet_data["name"])
        for good_name, price in planet_data["market"].items():
            if good_name in goods:
                planet.add_good(goods[good_name], price)
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

    return player, planets

def game_loop(player, planets):
    """The main game loop."""
    while True:
        print(f"\n--- {player.location.name} ---")
        print(f"Credits: {player.credits}")
        print(f"Fuel: {player.ship.fuel}/{player.ship.fuel_capacity}")
        print(f"Cargo: {[good.name for good in player.ship.cargo]}")

        # Display market
        print("\nMarket:")
        for good, price in player.location.market.items():
            print(f"- {good.name}: {price} credits")

        # Get player action
        action = input("\nWhat do you want to do? (travel, buy, sell, quit): ").lower()

        if action == "quit":
            print("Thanks for playing!")
            sys.exit()
        elif action == "travel":
            travel(player, planets)
        elif action == "buy":
            buy_goods(player)
        elif action == "sell":
            sell_goods(player)
        else:
            print("Invalid action.")

def travel(player, planets):
    """Handles player travel between planets."""
    destinations = [p for p in planets if p != player.location]
    print("\nAvailable destinations:")
    for i, planet in enumerate(destinations):
        print(f"{i + 1}. {planet.name}")

    try:
        choice = int(input("Choose a destination (number): ")) - 1
        if 0 <= choice < len(destinations):
            destination = destinations[choice]
            fuel_cost = 20  # Static fuel cost for now
            if player.ship.fuel >= fuel_cost:
                player.ship.fuel -= fuel_cost
                player.location = destination
                print(f"Traveled to {destination.name}.")
            else:
                print("Not enough fuel to travel.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid choice.")

def buy_goods(player):
    """Handles buying goods from a planet's market."""
    good_name = input("What do you want to buy? ").lower()

    found_good = None
    price = 0
    for good, p in player.location.market.items():
        if good.name.lower() == good_name:
            found_good = good
            price = p
            break

    if found_good:
        if player.credits >= price:
            if player.ship.add_cargo(found_good):
                player.credits -= price
                print(f"Bought {found_good.name} for {price} credits.")
            else:
                print("Cargo hold is full.")
        else:
            print("Not enough credits.")
    else:
        print("Good not found in this market.")

def sell_goods(player):
    """Handles selling goods from the player's cargo."""
    good_name = input("What do you want to sell? ").lower()

    # Find the good in cargo without removing it yet
    good_to_sell = None
    for good in player.ship.cargo:
        if good.name.lower() == good_name:
            good_to_sell = good
            break

    if good_to_sell:
        price = player.location.market.get(good_to_sell)

        if price is not None:
            player.credits += price
            player.ship.remove_cargo(good_name) # Remove from cargo only after successful sale
            print(f"Sold {good_to_sell.name} for {price} credits.")
        else:
            print("This planet doesn't buy this good.")
    else:
        print("Good not found in cargo.")

if __name__ == "__main__":
    player, planets = setup_game()
    game_loop(player, planets)
