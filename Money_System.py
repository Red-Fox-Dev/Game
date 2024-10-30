class MoneySystem:

    def __init__(self, init_amount=0, reward=100):
        self.balance = init_amount  # เงินเริ่มต้น
        self.reward = reward  # เงินที่ได้รับต่อเทิร์น
        self.is_capturing = True  # สถานะการยึดจุด
        self.capture_count = 0  # ตัวนับจำนวนครั้งการยึดจุดทั้งหมด
        self.capture_limit = 2000  # เงินสูงสุดที่สามารถเก็บได้ต่อจุด
        self.current_capture_earnings = 0  # เก็บเงินสะสมของจุดปัจจุบัน

    def add_money(self, init_amount):  # รับเงินเริ่มต้น
        if init_amount > 0:
            self.balance = init_amount
            return f"Total Amount : {self.balance} $"

    def capture_point(self):  # ยึดจุด
        messages = []  # เก็บผลลัพธ์จากการยึดจุดแต่ละรอบ
        while self.is_capturing and self.capture_count < 3:  # ทำงานต่อไปจนกว่าจะครบ 3 จุด
            if self.current_capture_earnings >= self.capture_limit:
                messages.append(f"This point has reached the maximum resource limit of {self.capture_limit} $. Moving to next point.")
                self.capture_count += 1  # ยึดจุดถัดไป
                self.current_capture_earnings = 0  # เริ่มนับเงินที่จุดใหม่

                # หยุดการยึดจุดเมื่อครบ 3 จุด
                if self.capture_count >= 3:
                    messages.append("Maximum capture points reached. Capture point stopped.")
                    break

            elif self.reward > 0:
                # ตรวจสอบให้แน่ใจว่าไม่เกิน 2000 ต่อจุด
                if self.current_capture_earnings + self.reward > self.capture_limit:
                    self.reward = self.capture_limit - self.current_capture_earnings
                self.balance += self.reward
                self.current_capture_earnings += self.reward
                messages.append(f"Capture point successful! Earned: {self.reward} $ Total Balance: {self.balance} $ (Point Earnings: {self.current_capture_earnings} $)")

            else:
                messages.append("No reward specified for capture point.")

        return "\n".join(messages)  # ส่งกลับข้อความทั้งหมดที่เก็บในลูป

    def subtract_money(self, cost):  # หักค่าใช้จ่าย unit / สิ่งปลูกสร้าง
        if cost > 0:
            if self.balance >= cost:
                self.balance -= cost
                return f"Spend money: {cost} $ Total Amount: {self.balance} $"
            else:
                return "Not enough money !!!"

    # ยูนิตแต่ละตัว
    def sword_soldier(self, cost):
        return f"Purchase a sword soldier at the price of {cost} $ {self.subtract_money(cost)}"

    def gun_soldier(self, cost):
        return f"Purchase a gun soldier at the price of {cost} $ {self.subtract_money(cost)}"

    def mage_soldier(self, cost):
        return f"Purchase a mage soldier at the price of {cost} $ {self.subtract_money(cost)}"

    def cavalry(self, cost):
        return f"Purchase a cavalry at the price of {cost} $ {self.subtract_money(cost)}"

    def stone_thrower(self, cost):
        return f"Purchase a stone thrower at the price of {cost} $ {self.subtract_money(cost)}"

    def horse_carriage(self, cost):
        return f"Purchase a horse carriage at the price of {cost} $ {self.subtract_money(cost)}"

    def dragon_rider(self, cost):
        return f"Purchase a dragon rider at the price of {cost} $ {self.subtract_money(cost)}"

    def naval(self, cost):
        return f"Purchase a naval soldier at the price of {cost} $ {self.subtract_money(cost)}"

    def build_structure(self, cost):
        return f"Build a structure at the price of {cost} $ {self.subtract_money(cost)}"

    def check_balance(self):
        return f"Total Amount: {self.balance} $"

# เริ่มเกม
player_money = MoneySystem(init_amount=0, reward=100)
print(player_money.add_money(250))

# ยึดจุดเพื่อรับเงิน
print(player_money.capture_point())

# หักค่าซื้อ Unit / สิ่งปลูกสร้าง
print(player_money.sword_soldier(50))
print(player_money.gun_soldier(80))
print(player_money.mage_soldier(150))
print(player_money.cavalry(200))
print(player_money.stone_thrower(350))
print(player_money.horse_carriage(380))
print(player_money.dragon_rider(450))
print(player_money.naval(500))

# สิ่งปลูกสร้าง
print(player_money.build_structure(50))

# ตรวจสอบยอดเงิน
print(player_money.check_balance())

