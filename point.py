import pygame

# กำหนดค่าคงที่สำหรับขนาดของกริดและหน้าจอ
GRID_WIDTH, GRID_HEIGHT = 40, 24
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 720
FPS = 60

# กำหนดสีพื้นฐานสำหรับการใช้งานในเกม
BLACK, WHITE, GREEN = (0, 0, 0), (255, 255, 255), (0, 255, 0)

# คลาส MoneyFarmSpot ใช้สร้างจุดฟาร์มเงิน
class MoneyFarmSpot:
    def __init__(self, x, y):
        self.x, self.y = x, y  # กำหนดตำแหน่งจุดฟาร์มเงิน
        self.color = GREEN  # สีของจุดฟาร์มเงิน
        # คำนวณขนาดของแต่ละช่องตามขนาดของหน้าจอและกริด
        self.tile_size = min(SCREEN_WIDTH // GRID_WIDTH, SCREEN_HEIGHT // GRID_HEIGHT)

    #วาดจุดฟาร์มเงิน
    def draw(self, screen):
        rect = pygame.Rect(self.x * self.tile_size, self.y * self.tile_size, self.tile_size, self.tile_size)
        pygame.draw.rect(screen, self.color, rect)

#วาดกริดบนหน้าจอ
def draw_grid(screen):
    tile_size = min(SCREEN_WIDTH // GRID_WIDTH, SCREEN_HEIGHT // GRID_HEIGHT)  # คำนวณขนาดของช่อง
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            pygame.draw.rect(screen, WHITE, rect, 1)  # วาดกรอบช่องสีขาว

# เริ่มต้น Pygame และตั้งค่าหน้าต่าง
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # กำหนดขนาดหน้าจอ
pygame.display.set_caption("Money Farm Game")  # ตั้งชื่อหน้าต่าง
clock = pygame.time.Clock()  # สร้างนาฬิกาเพื่อควบคุม FPS

# สร้างรายการจุดฟาร์มเงินที่กำหนดตำแหน่งในกริด
farm_spots = [MoneyFarmSpot(10, 3), MoneyFarmSpot(6, 5), MoneyFarmSpot(35, 20)]

# ลูปหลักของเกม
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # ตรวจสอบว่ามีการปิดหน้าต่างหรือไม่
            running = False

    screen.fill(BLACK)  # ล้างหน้าจอด้วยสีดำ
    draw_grid(screen)  # วาดกริดบนหน้าจอ

    # วาดจุดฟาร์มเงินแต่ละจุดบนหน้าจอ
    for spot in farm_spots:
        spot.draw(screen)

    pygame.display.flip()  # อัปเดตหน้าจอ
    clock.tick(FPS)  # จำกัดอัตราเฟรมตามค่า FPS

pygame.quit()

