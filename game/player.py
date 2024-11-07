class Player:
    def __init__(self, name, starting_money=250):
        self.name = name
        self.money = starting_money
        self.units = []  # รายการยูนิตของผู้เล่น

    def add_unit(self, unit):
        self.units.append(unit)

    def update_money(self, amount):
        self.money += amount
