import robotic as ry
import random
import json
import os

class Obstacle:
    """
    Represents an obstacle in the maze environment.
    """
    def __init__(self, config, name, shape_type, size, color, position):
        unique_id = str(random.randint(1000, 9999))  # Generate a random 4-digit ID
        self.name = f"{name}_{unique_id}"
        self.config = config
        self.shape_type = shape_type
        self.size = size
        self.color = color
        self.position = position
        self.create_object()

    def create_object(self):
        """
        Adds the obstacle to the configuration.
        """
        frame = self.config.addFrame(self.name)
        frame.setShape(self.shape_type, self.size)
        frame.setColor(self.color)
        frame.setPosition(self.position)

    @classmethod
    def from_dict(cls, config, data):
        """
        Creates an obstacle object from a dictionary representation.
        """
        shape_type_mapping = {'ssBox': ry.ST.ssBox}
        shape_type = shape_type_mapping[data['shape_type']]
        return cls(config, data['name'], shape_type, data['size'], data['color'], data['position'])

    def to_dict(self):
        """
        Converts the obstacle into a dictionary format.
        """
        return {
            'name': self.name,
            'shape_type': str(self.shape_type).split('.')[-1],  # Save shape_type as string
            'size': self.size,
            'color': self.color,
            'position': self.position
        }


class Maze:
    """
    Represents the maze structure, including walls, goal objects, and obstacles.
    """
    def __init__(self, config, size=16, scale=1/3, wall_height=1, wall_length=1, floor_size=20, center_position=[0, 0]):
        self.config = config
        self.obstacles = []
        self.size = size
        self.scale = scale
        self.wall_height = wall_height
        self.wall_length = wall_length
        self.maze_size = self.size * self.wall_length
        self.center_position = center_position
        self.custom_walls = {}
        self.wall_id_counter = 1
        self.create_floor()
        self.create_maze()

    def create_floor(self):
        """
        Creates the floor of the maze.
        """
        floor_color = [0.8, 0.8, 0.8]  # Light gray color for the floor
        floor_thickness = 0.1
        floor_size = [self.maze_size, self.maze_size, floor_thickness, 0.1]
        center_x, center_y = self.center_position
        floor_position = [center_x, center_y, -floor_thickness / 2]
        floor = Obstacle(self.config, 'floor', ry.ST.ssBox, floor_size, floor_color, floor_position)
        self.obstacles.append(floor)

    def add_wall(self, name, position, size, color):
        """
        Adds a wall to the maze at a given position.
        """
        wall = Obstacle(self.config, name, ry.ST.ssBox, size, color, position)
        self.obstacles.append(wall)
        self.wall_id_counter += 1

    def create_maze(self):
        """
        Creates the maze perimeter using walls.
        """
        wall_color = [0.35, 0.16, 0.14]  # Dark brown color for the wall
        cube_size = [self.wall_length, self.wall_length, self.wall_height, 0.1]
        offset_x = -self.maze_size / 2
        offset_y = -self.maze_size / 2

        # Create top and bottom perimeter walls
        for i in range(self.size + 2):
            x = offset_x + i * self.wall_length - self.wall_length / 2
            self.add_wall(f'top_wall_{i}', [x, offset_y - self.wall_length / 2, self.wall_height / 2], cube_size, wall_color)
            self.add_wall(f'bottom_wall_{i}', [x, offset_y + self.maze_size + self.wall_length / 2, self.wall_height / 2], cube_size, wall_color)

        # Create left and right perimeter walls
        for i in range(self.size + 2):
            y = offset_y + i * self.wall_length - self.wall_length / 2
            self.add_wall(f'left_wall_{i}', [offset_x - self.wall_length / 2, y, self.wall_height / 2], cube_size, wall_color)
            self.add_wall(f'right_wall_{i}', [offset_x + self.maze_size + self.wall_length / 2, y, self.wall_height / 2], cube_size, wall_color)

    def add_custom_wall(self, start_coords, direction, length):
        """
        Adds a custom wall to the maze in a given direction with a specified length.
        """
        wall_color = [0.25, 0.25, 0.25]
        cube_size = [self.wall_length, self.wall_length, self.wall_height, 0.1]
        x, y = start_coords
        if direction == 'horizontal':
            for i in range(length):
                name = f'custom_wall_{self.wall_id_counter}'
                self.add_wall(name, [x + i * self.wall_length, y, self.wall_height / 2], cube_size, wall_color)
                self.wall_id_counter += 1
        elif direction == 'vertical':
            for i in range(length):
                name = f'custom_wall_{self.wall_id_counter}'
                self.add_wall(name, [x, y + i * self.wall_length, self.wall_height / 2], cube_size, wall_color)
                self.wall_id_counter += 1

    def add_goal_object(self, coord):
        """
        Adds the goal object to the maze.
        """
        position = [coord[0], coord[1], 0.2]
        self.goal_object = Obstacle(self.config, 'goal_object', ry.ST.ssBox, [0.3, 0.3, 0.3, 0.1], [0, 0, 1], position)
        self.obstacles.append(self.goal_object)
        print("Goal object added.")

    def add_final_object(self, coord):
        """
        Adds the final object to the maze.
        """
        position = [coord[0], coord[1], 0.3]
        self.final_object = Obstacle(self.config, 'final_object', ry.ST.ssBox, [0.4, 0.4, 0.4, 0.1], [1, 1, 0], position)
        self.obstacles.append(self.final_object)
        print("Final object added.")

    def save_maze(self, file_path, robot=None):
        """
        Saves the maze configuration and optionally a robot to a JSON file.
        """
        maze_data = {
            'size': self.size,
            'scale': self.scale,
            'wall_height': self.wall_height,
            'wall_length': self.wall_length,
            'maze_size': self.maze_size,
            'center_position': self.center_position,
            'wall_id_counter': self.wall_id_counter,
            'obstacles': [obs.to_dict() for obs in self.obstacles],
            'custom_walls': [wall.to_dict() for wall in self.custom_walls.values()]
        }
        if robot:
            maze_data['robot_position'] = robot.position
            maze_data['robot_model'] = robot.model
            maze_data['robot_quaternion'] = robot.quaternion
        with open(file_path, 'w') as f:
            json.dump(maze_data, f, indent=4)
        print(f"Maze saved to {file_path}")

    def load_maze(self, file_path):
        """
        Loads a maze configuration from a JSON file.
        """
        with open(file_path, 'r') as f:
            maze_data = json.load(f)
        self.size = maze_data['size']
        self.scale = maze_data['scale']
        self.wall_height = maze_data['wall_height']
        self.wall_length = maze_data['wall_length']
        self.maze_size = maze_data['maze_size']
        self.center_position = maze_data['center_position']
        self.wall_id_counter = maze_data['wall_id_counter']
        self.config.clear()

        # Load obstacles
        self.obstacles = []  # Clear existing obstacles
        for obs_data in maze_data['obstacles']:
            obstacle = Obstacle.from_dict(self.config, obs_data)
            self.obstacles.append(obstacle)

        # Load custom walls
        self.custom_walls = {}  # Clear existing custom walls
        if 'custom_walls' in maze_data:
            for wall_data in maze_data['custom_walls']:
                wall = Obstacle.from_dict(self.config, wall_data)
                self.custom_walls[wall.name] = wall

        print(f"Maze loaded from {file_path}")


class Robot:
    """
    Represents the robot in the simulation.
    """
    def __init__(self, config, position, model, quaternion):
        self.config = config
        self.position = position
        self.model = model
        self.quaternion = quaternion
        self.create_robot()

    def create_robot(self):
        """
        Creates the robot and adds it to the configuration.
        """
        robot_file = ry.raiPath(f"{self.model}/{self.model}.g")
        self.config.addFile(robot_file).setPosition(self.position).setQuaternion(self.quaternion)
        print("Robot successfully added.")

def check_collision(new_wall, existing_walls):
    """
    Check if the new wall collides with any existing walls.

    Parameters:
    new_wall (tuple): The boundary of the new wall (x1, y1, x2, y2).
    existing_walls (list): List of boundaries of existing walls.

    Returns:
    bool: True if there is a collision, False otherwise.
    """
    x1, y1, x2, y2 = new_wall

    for wall in existing_walls:
        wx1, wy1, wx2, wy2 = wall
        # Check for overlap using axis-aligned bounding box (AABB) collision detection
        if x1 < wx2 and x2 > wx1 and y1 < wy2 and y2 > wy1:
            return True  # Collision detected

    return False  # No collision

def generate_random_walls(maze, num_walls):
    """
    Generate random wall configurations within the maze without collisions and within maze borders.

    Parameters:
    maze (Maze): An instance of the Maze class.
    num_walls (int): Number of random walls to generate.
    """
    existing_walls = []  # Store the boundaries of all added walls

    for _ in range(num_walls):
        attempts = 0
        max_attempts = 100  # Prevent infinite loops

        while attempts < max_attempts:
            # Generate random starting coordinates within the maze bounds (considering wall length)
            x = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)
            y = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)

            # Randomly choose direction and length
            direction = random.choice(['horizontal', 'vertical'])
            length = random.randint(1, 3)  # Random wall length between 1 and 3 cells

            # Calculate the boundaries of the proposed wall
            if direction == 'horizontal':
                wall_boundary = (x, y, x + length * maze.wall_length, y + maze.wall_height)
            else:  # vertical
                wall_boundary = (x, y, x + maze.wall_length, y + length * maze.wall_length)

            # Check for collisions with existing walls and maze borders
            if not check_collision(wall_boundary, existing_walls):
                # No collision, add the wall and record its boundary
                maze.add_custom_wall([x, y], direction, length)
                existing_walls.append(wall_boundary)
                break  # Proceed to the next wall
            else:
                attempts += 1

        if attempts == max_attempts:
            print(f"Failed to place wall after {max_attempts} attempts.")

    print(f"{num_walls} random walls added without collisions.")


def generate_and_save_random_mazes(num_mazes, num_walls, folder_path):
    """
    Generate random maze configurations with non-colliding walls and save them as separate JSON files.

    Parameters:
    num_mazes (int): Number of random mazes to generate.
    num_walls (int): Number of random walls to generate per maze.
    folder_path (str): Path to the folder where maze files will be saved.
    """
    # Ensure the folder exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i in range(1, num_mazes + 1):
        config = ry.Config()  # Create a new config for each maze
        maze = Maze(config, center_position=[0, 0], wall_height=1, wall_length=1, floor_size=20)
        generate_random_walls(maze, num_walls)

        # Add random goal and final object positions within maze bounds
        goal_x = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)
        goal_y = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)
        final_x = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)
        final_y = random.uniform(-maze.maze_size / 2 + maze.wall_length, maze.maze_size / 2 - maze.wall_length)

        maze.add_goal_object([goal_x, goal_y])
        maze.add_final_object([final_x, final_y])

        file_name = f"maze_{i}.json"
        file_path = os.path.join(folder_path, file_name)
        maze.save_maze(file_path, robot=None)
        print(f"Random maze {i} saved to {file_name}")


def load_maze_and_add_robot(maze_file_path):
    """
    Load a maze from a file, add a robot to the center of the maze, and visualize it.

    Parameters:
    maze_file_path (str): The path to the JSON file containing the maze configuration.
    """
    config = ry.Config()  # Create a new configuration instance
    maze = Maze(config)  # Create an empty maze object

    # Load the maze configuration from the JSON file
    maze.load_maze(maze_file_path)

    # Add the robot to the center of the loaded maze
    center_x, center_y = maze.center_position
    robot_position = [center_x, center_y, 0]  # Assuming ground level
    robot = Robot(config, position=robot_position, model="panda", quaternion=[1, 0, 0, 0])

    # Visualize the loaded maze with the robot
    config.view()

    # Keep the window open until user input
    input("Press ENTER to exit...")


if __name__ == "__main__":
    # Example: Load a specific maze and add a robot
    maze_file_path = "random_mazes/maze_1.json"  # Change to your desired maze file path
    load_maze_and_add_robot(maze_file_path)

    # Example: To generate and save mazes instead, uncomment the following lines:

    """
    num_mazes = 30  # Number of mazes to generate
    num_walls_per_maze = 10  # Number of walls per maze
    folder_name = "random_mazes"  # Folder to save the mazes

    generate_and_save_random_mazes(num_mazes, num_walls_per_maze, folder_name)
    """

