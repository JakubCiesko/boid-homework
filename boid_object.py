import pyglet
import math
import random
from pyglet.window import key
from scipy.spatial import KDTree


pyglet.resource.reindex()
attack_sound = pyglet.resource.media('sounds/bird_sound.mp3')


def get_angle_between_vectors(v1, v2):
    a = math.sqrt(v1[0] ** 2 + v1[1] ** 2) * math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    b = v2[0] * v1[0] + v2[1] * v1[1]
    if a != 0 and abs(b / a) < 1:
        angle = math.degrees(math.acos(b / a))
    else:
        angle = 0 if a != 0 and b / a > 0 else 180
    return angle


class BoidShape(pyglet.shapes.Sector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._change_constant = random.randint(5, 25)
        self.velocity = random.choice([0.5, 0.80, 0.30, 0.40, 0.7, 1]) * 15 * self._change_constant
        self.rotation = random.choice([0.5, 1]) * 5 * self._change_constant
        self.counter = 0
        self.rotation_speed = 60*self._change_constant
        self.smart = False
        self.hunting = False

    def find_closest(self, other_boids):
        positions = [boid.position for boid in other_boids]
        if positions:
            tree = KDTree(positions)
            indices = tree.query_ball_point(self.position, r=200)
            if indices:
                closest_boid = other_boids[indices[0]]
                other_close_boids = [other_boids[index] for index in indices[1:]] if len(indices) >= 2 else []
                return closest_boid, math.dist(self.position, closest_boid.position), other_close_boids
        return None, 0, []

    def align(self, other_boid, dt):
        if math.dist(self.position, other_boid.position) <= 200:
            rotation_speed = (self.rotation - other_boid.rotation)
            if (abs(self.rotation - other_boid.rotation)) > 2:
                self.rotation -= rotation_speed*dt

    def handle_collision(self, other, dt):
        max_radius = 150
        field_of_view = range(100)
        def distance(x): return math.dist(self.position, x)
        other_vector = (math.cos(math.radians(other.rotation)), math.sin(math.radians(other.rotation)))
        vector = (math.cos(math.radians(self.rotation)), math.sin(math.radians(self.rotation)))
        displacement_vector = (other.x-self.x, other.y-self.y)
        point_of_intersection = self.get_intersection(other.position, other_vector)

        vel_dis_vector_angle = get_angle_between_vectors(vector, displacement_vector)
        distance_to_collision = distance(point_of_intersection) if point_of_intersection else distance(other.position)
        distance_to_other = distance(other.position)
        if (max_radius > distance_to_collision or max_radius > distance_to_other) and (int(abs(vel_dis_vector_angle)) in field_of_view):
            self.rotation += 2*self._change_constant*dt

    def navigate_towards_center(self, center):
        if center is None:
            return
        x, y = center[0], center[1]
        x1, y1 = self.position
        vector = (math.cos(math.radians(self.rotation)), math.sin(math.radians(self.rotation)))
        displacement_vector = (x1-x, y1-y)
        alpha = get_angle_between_vectors(vector, displacement_vector) - self.rotation
        self.rotation += alpha/self.rotation_speed

    def calculate_velocities(self):
        rot = math.radians(self.rotation)
        return self.velocity * math.cos(rot), self.velocity * math.sin(rot)

    def update(self, closest_boid, center, game_window, rules, dt, player=None):
        handle_collision, align, navigate_toward_center, hunt_player = rules.values()
        self.counter += 1
        if not self.counter % (self._change_constant*20):
            self.rotation += random.choice([0.5, 1, 1.5, 2]) * self._change_constant*0.5
        self.bounce_off_boundary(game_window)
        if navigate_toward_center and center:
            self.navigate_towards_center(center)
        if handle_collision and closest_boid:
            self.handle_collision(closest_boid, dt)
        if align and closest_boid:
            self.align(closest_boid, dt)
        if hunt_player and player:
            self.hunt_player(player, dt)
        vx, vy = self.calculate_velocities()
        self.x += vx * dt
        self.y += vy * dt

    def bounce_off_boundary(self, game_window, player=False):
        xmax, ymax = game_window.width, game_window.height
        max_radius = 150 if not player else 50
        corners = {'p1': ([0, 0], [1, 0], [0, 1]),
                   'p2': ([0, ymax], [0, -1], [1, 0]),
                   'p3': ([xmax, ymax], [-1, 0], [0, -1]),
                   'p4': ([xmax, 0], [-1, 0], [0, 1])}

        quad = (self.rotation//90) % 4 + 1
        if quad == 1:
            p, v1, v2 = corners['p3']
        if quad == 2:
            p, v1, v2 = corners['p2']
        if quad == 3:
            p, v1, v2 = corners['p1']
        if quad == 4:
            p, v1, v2 = corners['p4']
        vectors = [v1, v2]
        for vector in vectors:
            v = vector
            intersection = self.get_intersection(p, v)
            if intersection:
                distance = math.dist(intersection, self.position)
                if distance < max_radius:
                    self.rotation += 15+self._change_constant/2
                    if player:
                        self.velocity = 0

    def get_intersection(self, point2, vector2):
        line1 = [[self.x, self.y], [self.x+math.cos(math.radians(self.rotation)), self.y+math.sin(math.radians(self.rotation))]]
        line2 = [[point2[0], point2[1]], [point2[0] + vector2[0], point2[1] + vector2[1]]]
        xdiff = (self.x - (self.x+math.cos(math.radians(self.rotation))), point2[0] - (point2[0] + vector2[0]))
        ydiff = (self.y - (self.y+math.sin(math.radians(self.rotation))), point2[1] - (point2[1] + vector2[1]))

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)
        if div == 0:
            return None

        d = (det(*line1), det(*line2))
        x = det(d, xdiff) / div
        y = det(d, ydiff) / div
        return abs(x), abs(y)

    def hunt_player(self, player, dt):
        player_boid_distance = math.dist(player.position, self.position)
        if not player.check_death():
            if 300 > player_boid_distance > 30:
                if not self.hunting:
                    self.hunting = True
                    attack_sound.play()
                playerx, playery = player.position
                playervx, playervy = player.calculate_velocities()
                playerx_extended = playerx + 2*playervx*dt
                playery_extended = playery + 2*playervy*dt
                x, y = self.position
                #vector = (math.cos(math.radians(self.rotation)), math.sin(math.radians(self.rotation)))
                displacement_vector = (playerx_extended-x, playery_extended-y) if self.smart else (playerx - x, playery - y)
                #alpha = get_angle_between_vectors(vector, displacement_vector)
                self.rotation = math.degrees(math.atan2(displacement_vector[1], displacement_vector[0]))
            elif player_boid_distance < 30:
                player.health -= 1
            else:
                self.hunting = False


class PlayerBoid(BoidShape):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_handler = key.KeyStateHandler()
        self.velocity = 0
        self.health = 100

    def update(self, dt, game_window, *args, **kwargs):
        self.bounce_off_boundary(game_window=game_window, player = True)
        if self.key_handler[key.LEFT]:
            self.rotation += 5
        if self.key_handler[key.RIGHT]:
            self.rotation -= 5
        if self.key_handler[key.UP]:
            self.velocity += 20 if self.velocity < 500 else 0
        elif self.key_handler[key.DOWN]:
            self.velocity -= 20 if self.velocity > -500 else 0
        else:
            self.velocity = 0
        vx, vy = self.calculate_velocities()
        self.x += vx*dt
        self.y += vy*dt

    def check_death(self):
        if self.health <= 0:
            return True
        return False


class Flock:
    def __init__(self):
        self.boids_in_flock = list()

    def calculate_center(self):
        x,y = list(), list()
        for boid in self.boids_in_flock:
            x.append(boid.position[0])
            y.append(boid.position[1])
        return (sum(x)/len(self.boids_in_flock),sum(y)/len(self.boids_in_flock))

    def add_boid(self, boid):
        self.boids_in_flock.append(boid)

    def add_boids(self, boids):
        self.boids_in_flock.extend(boids)

    def remove_boid(self, boid):
        self.boids_in_flock.remove(boid)

    def update(self, dt):
        for i in range(len(self.boids_in_flock)):
            pre = self.boids_in_flock[:i]
            post = self.boids_in_flock[i:]
            other = pre+post
            for other_boid in other:
                print(math.dist(self.boids_in_flock[i].position,other_boid.position))
        pass


class Shot(BoidShape):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.velocity = 0
        self.rotation = 0

    def update(self, dt):
        vx, vy = self.calculate_velocities()
        self.x += vx*dt
        self.y += vy*dt