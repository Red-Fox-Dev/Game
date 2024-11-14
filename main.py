from game.game import Game
from game.game_config import GameConfig

if __name__ == "__main__":
    # เริ่มเกมด้วยการตั้งค่าคอนฟิก
    config = GameConfig()
    game = Game(config)
    game.run()