import sys

class Good:
    """Represents a good that can be traded."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

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

def setup_game():
    """Sets up the initial game state."""
    # Create goods
    water = Good("Water")
    food = Good("Food")
    minerals = Good("Minerals")

    # Create planets
    terra = Planet("Terra")
    mars = Planet("Mars")
    europa = Planet("Europa")

    # Add goods to markets
    terra.add_good(water, 100)
    terra.add_good(food, 150)
    terra.add_good(minerals, 200)

    mars.add_good(water, 120)
    mars.add_good(food, 130)
    mars.add_good(minerals, 180)

    europa.add_good(water, 90)
    europa.add_good(food, 160)
    europa.add_good(minerals, 220)

    planets = [terra, mars, europa]

    # Create ship and player
    ship = Ship()
    player = Player("Captain", ship, terra)

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

    good_to_sell = player.ship.remove_cargo(good_name)

    if good_to_sell:
        price = None
        for good, p in player.location.market.items():
            if good.name.lower() == good_to_sell.name.lower():
                price = p
                break

        if price is not None:
            player.credits += price
            print(f"Sold {good_to_sell.name} for {price} credits.")
        else:
            # This case should ideally not happen if all planets trade all goods
            print("This planet doesn't buy this good.")
            # Put it back in cargo
            player.ship.add_cargo(good_to_sell)
    else:
        print("Good not found in cargo.")

if __name__ == "__main__":
    player, planets = setup_game()
    game_loop(player, planets)
