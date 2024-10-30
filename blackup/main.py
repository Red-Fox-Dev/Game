import pygame
from game import Game  # นำเข้าคลาส Game จากโมดูล game

if __name__ == "__main__":  # เช็คว่าไฟล์นี้ถูกเรียกใช้งานโดยตรง
    pygame.init()  # เริ่มต้น Pygame

    game = Game()  # สร้างอ็อบเจ็กต์ game จากคลาส Game
    game.run()  # เรียกใช้ฟังก์ชัน run() เพื่อเริ่มเกม

    pygame.quit()  # ปิด Pygame เมื่อเกมจบ
