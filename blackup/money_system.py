class MoneySystem:
    def __init__(self, init_amount_player1: int, init_amount_player2: int, reward: int, build_cost: int):
        self.balance = {1: init_amount_player1, 2: init_amount_player2}  # เงินของผู้เล่น 1 และ 2
        self.reward = reward  # เงินที่ได้รับต่อเทิร์น
        self.build_cost = build_cost  # ค่าใช้จ่ายในการสร้างอาคาร
        self.capture_count = {1: 0, 2: 0}  # ตัวนับจำนวนครั้งการยึดจุด
        self.capture_limit = 2000  # เงินสูงสุดที่สามารถเก็บได้ต่อจุด
        self.current_capture_earnings = {1: 0, 2: 0}  # เก็บเงินสะสมของจุดปัจจุบัน

    def add_money(self, amount: int, player: int):
        """ เพิ่มเงินเข้าบัญชีของผู้เล่น """
        if amount > 0:  # ตรวจสอบว่าเงินที่เพิ่มเข้ามามากกว่า 0
            self.balance[player] += amount  # เพิ่มเงินเข้าบัญชี
            return f"Player {player} Total Amount: {self.balance[player]} $"  # คืนค่าข้อความแสดงยอดเงินรวม

    def capture_point(self, player: int):
        """ ยึดจุดเพื่อรับเงิน """
        messages = []  # สร้างลิสต์สำหรับเก็บข้อความ
        while self.capture_count[player] < 3:  # ตรวจสอบจำนวนครั้งการยึดจุด
            if self.current_capture_earnings[player] >= self.capture_limit:  # ถ้าเงินสะสมถึงขีดจำกัด
                messages.append(f"Player {player}: Point reached max limit. Moving to next point.")
                self.capture_count[player] += 1  # เพิ่มจำนวนครั้งการยึดจุด
                self.current_capture_earnings[player] = 0  # รีเซ็ตเงินสะสม

                if self.capture_count[player] >= 3:  # ถ้าถึงจำนวนครั้งสูงสุด
                    messages.append(f"Player {player}: Maximum capture points reached.")
                    break
            else:
                earnings = min(self.reward, self.capture_limit - self.current_capture_earnings[player])
                self.balance[player] += earnings  # เพิ่มเงินจากรางวัลเข้าบัญชี
                self.current_capture_earnings[player] += earnings  # เพิ่มเงินสะสม
                messages.append(f"Player {player}: Captured point! Earned: {earnings} $ Total: {self.balance[player]} $")

        return "\n".join(messages)  # คืนค่าข้อความทั้งหมดในลิสต์

    def subtract_money(self, cost: int, player: int) -> bool:
        """ หักเงินออกจากบัญชีของผู้เล่น """
        if cost > 0 and self.balance[player] >= cost:  # ตรวจสอบว่าเงินที่หักมากกว่า 0 และมีเงินพอ
            self.balance[player] -= cost  # หักเงินออก
            return True  # คืนค่าความสำเร็จ
        return False  # คืนค่าความล้มเหลว

    def create_unit(self, cost: int, player: int) -> bool:
        """ สร้างยูนิต """
        if self.balance[player] >= cost:
            self.balance[player] -= cost
            return True
        return False

    def check_balance(self, player: int) -> str:
        """ ตรวจสอบยอดเงินของผู้เล่น """
        return f"Player {player} Total Amount: {self.balance[player]} $"

    def amount(self, player: int) -> int:
        """ ให้สามารถเข้าถึงยอดเงินของผู้เล่นได้ """
        return self.balance[player]  # คืนค่าของยอดเงิน

    def end_turn(self, player: int):
        """ เพิ่มเงินเมื่อสิ้นสุดเทิร์น """
        self.balance[player] += self.reward
