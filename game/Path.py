from queue import PriorityQueue
# คลาสสำหรับค้นหาเส้นทางใน Isometric Map
class PathFinder:
    def __init__(self, iso_map):
        """
        เริ่มต้นการค้นหาเส้นทาง
        
        :param iso_map: แผนที่ Isometric ที่ใช้ในการค้นหาเส้นทาง
        """
        self.iso_map = iso_map
        # กำหนดทิศทางที่สามารถเคลื่อนที่ได้ (4 ทิศทางหลัก + 4 ทิศทางทแยง)
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0),  # แนวตั้งและแนวนอน
                          (1, 1), (-1, -1), (1, -1), (-1, 1)]  # แนวทแยง

    def heuristic(self, a, b):
        """คำนวณระยะห่างแบบ Manhattan distance"""

        """
        คำนวณระยะห่างแบบ Manhattan distance
        
        :param a: จุดเริ่มต้น
        :param b: จุดปลายทาง
        :return: ระยะทางโดยประมาณ
        """

        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(self, pos):
        """หา tile ที่สามารถเดินไปได้รอบๆ ตำแหน่งปัจจุบัน"""

        """
        :param pos: ตำแหน่งปัจจุบัน
        :return: รายการตำแหน่งที่สามารถเดินได้
        """

        neighbors = []
        for dx, dy in self.directions:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            # ตรวจสอบว่าอยู่ในขอบเขตของแผนที่
            if (0 <= new_x < self.iso_map.tmx_data.width and 
                0 <= new_y < self.iso_map.tmx_data.height):
                # เช็คว่าสามารถเดินผ่านได้
                if self.is_walkable((new_x, new_y)):
                    neighbors.append((new_x, new_y))
        return neighbors

    def is_walkable(self, pos):
        """เช็คว่า tile นี้สามารถเดินผ่านได้หรือไม่"""

        """
        :param pos: ตำแหน่งที่ต้องการตรวจสอบ
        :return: True ถ้าสามารถเดินผ่านได้, False ถ้าถูกบล็อก
        """

        # ตรวจสอบคุณสมบัติของ tile จาก TMX
        for layer in self.iso_map.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                # ดึง Global ID ของ tile
                gid = layer.data[pos[1]][pos[0]]
                # ดึงคุณสมบัติของ tile
                props = self.iso_map.tmx_data.get_tile_properties_by_gid(gid)
                # ถ้ามี property 'blocked' และเป็น True ให้ถือว่าเดินไม่ได้
                if props and props.get('blocked', False):
                    return False
        return True

    def find_path(self, start, goal):
        """หาเส้นทางโดยใช้ A* algorithm"""

        """
        :param start: จุดเริ่มต้น
        :param goal: จุดหมายปลายทาง
        :return: รายการตำแหน่งของเส้นทาง
        """
        # Priority Queue สำหรับเก็บโหนดที่ต้องสำรวจ
        frontier = PriorityQueue()
        frontier.put((0, start))

        # เก็บบันทึกเส้นทางและต้นทุนการเดินทาง
        came_from = {start: None}
        cost_so_far = {start: 0}

        # อัลกอริทึม A* หลัก
        while not frontier.empty():
            current = frontier.get()[1]

            # หากถึงจุดหมายแล้ว
            if current == goal:
                break
            
            # คำนวณต้นทุนการเดินทาง
            for next_pos in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1

                # ปรับปรุงเส้นทางหากพบเส้นทางที่สั้นกว่า
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    
                    # คำนวณลำดับความสำคัญโดยรวมระยะทางกับค่า heuristic
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
        # ส่งคืนเส้นทางเฉพาะเมื่อเริ่มจากจุดเริ่มต้นเท่านั้น
        return path if path[0] == start else []
