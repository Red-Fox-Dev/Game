import math 
from queue import PriorityQueue
#เดินทาง
class PathFinder:
    def __init__(self, iso_map):
        self.iso_map = iso_map
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0),  # แนวตั้งและแนวนอน
                          (1, 1), (-1, -1), (1, -1), (-1, 1)]  # แนวทแยง

    def heuristic(self, a, b):
        """คำนวณระยะห่างแบบ Manhattan distance"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, pos):
        """หา tile ที่สามารถเดินไปได้รอบๆ ตำแหน่งปัจจุบัน"""
        neighbors = []
        for dx, dy in self.directions:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            if (0 <= new_x < self.iso_map.tmx_data.width and 
                0 <= new_y < self.iso_map.tmx_data.height):
                # เช็คว่าสามารถเดินผ่านได้
                if self.is_walkable((new_x, new_y)):
                    neighbors.append((new_x, new_y))
        return neighbors

    def is_walkable(self, pos):
        """เช็คว่า tile นี้สามารถเดินผ่านได้หรือไม่"""
        # ตรวจสอบคุณสมบัติของ tile จาก TMX
        for layer in self.iso_map.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                gid = layer.data[pos[1]][pos[0]]
                props = self.iso_map.tmx_data.get_tile_properties_by_gid(gid)
                if props and props.get('blocked', False):
                    return False
        return True

    def find_path(self, start, goal):
        """หาเส้นทางโดยใช้ A* algorithm"""
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not frontier.empty():
            current = frontier.get()[1]

            if current == goal:
                break

            for next_pos in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(goal, next_pos)
                    frontier.put((priority, next_pos))
                    came_from[next_pos] = current

        # สร้างเส้นทาง
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path if path[0] == start else []