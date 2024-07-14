from boid_object import BoidShape, Flock, PlayerBoid,  Shot
import pyglet
from pyglet.window import key
import math
import random


def load_sound():
    attack_sound = pyglet.media.load('sounds/bird_sound.mp3')
    hit_sound = pyglet.media.load('sounds/hit.mp3')
    death_sound = pyglet.media.load('sounds/death_sound.mp3')
    player_sound = pyglet.media.load('sounds/player_sound.mp3')
    shot_sound = pyglet.media.load('sounds/shot_sound.mp3')
    sound = pyglet.media.load('sounds/back_ground_music.mp3')
    sound_player = pyglet.media.Player()
    sound_player.loop = True
    sound_player.queue(sound)
    return attack_sound, hit_sound, death_sound, player_sound, shot_sound, sound_player


attack_sound, hit_sound, death_sound, player_sound, shot_sound, splayer = load_sound()
splayer.play()

radius = 8
pyglet.resource.reindex()

font_size = 15
color = [150, 50, 80, 255]


def rules_message(rule, MESSAGES, RULES, game_window, font_size, color):
    x, y = game_window.width//2, game_window.height//2
    if RULES[rule]:
        RULES[rule] = False
        MESSAGES.append(pyglet.text.Label(f'Rule "{" ".join(rule.split(sep="_")).title()}" deactivated',
                                          x=x, y=y,
                                          font_size=font_size,color=color))
    else:
        RULES[rule] = True
        MESSAGES.append(pyglet.text.Label(f'Rule "{" ".join(rule.split(sep="_")).title()}" activated',
                                          x=x, y=y,
                                          font_size=font_size,color=color))


def drawable_active_rules(rules, font_size, color, position=[0, 800], prefix='Active rules: ', split=True):
    string = prefix
    x = position[0] + 30+2*font_size
    y = position[1] - 2*font_size
    for rule in rules:
        add_string = f' {" ".join(rule.split(sep="_"))}' if split else f'{rule}'
        string += add_string
    return pyglet.text.Label(string, x=x, y=y, font_size=font_size, color=color)


draw_intersection = False
slow_down = False
BIRDS = False
draw_background = False
draw_boundaries = True
DRAW_PRIMITIVES = False
PLAYABLE = False
PLAYER = None
PLAYER_CREATED = False
RULES = {'handle_collision': False, 'align': False, 'navigate_toward_center': False, 'hunt_player': False}
MESSAGES = list()
CENTERS = dict()
game_window = pyglet.window.Window(width=1350, height=720)
game_window_limits = {'point1': [0, 0],
                      'point2': [game_window.width, game_window.height],
                      'vector1': [math.cos(0), math.sin(0)],
                      'vector2': [math.cos(math.pi/2), math.sin(math.pi/2)],
                      'vector3': [math.cos(math.pi), math.sin(math.pi)],
                      'vector4': [math.cos(3*math.pi/2), math.sin(3*math.pi/2)]}
if draw_boundaries:
    point1, point2 = game_window_limits['point1'], game_window_limits['point2']
    v1, v2, v3, v4 = game_window_limits['vector1'], game_window_limits['vector2'], game_window_limits['vector3'],game_window_limits['vector4']

main_batch = pyglet.graphics.Batch()


def load_game_screen_graphics():
    back_ground = pyglet.resource.image('obloha.png')
    back_ground_sprite = pyglet.sprite.Sprite(img=back_ground)
    return back_ground_sprite


background = load_game_screen_graphics() if draw_background else None
shots = list()


boids = list()
"""for boid in boids:
    print(boid.radius)
    boid.position = [random.randint(30, game_window.width), random.randint(30, game_window.height)]
    if slow_down:
        boid.velocity = 60
        boid.rotation = 75
"""

@game_window.event
def on_draw():
    game_window.clear()
    for shot in shots:
        shot.draw()
    active_rules = [rule_name for rule_name, value in RULES.items() if value]
    if active_rules:
        drawable_active_rules(active_rules, font_size, color, [0, game_window.height]).draw()
    if PLAYER:
        drawable_active_rules(['Health:', PLAYER.health], font_size, color, [0, game_window.height-1.5*font_size],prefix='', split=False).draw()
    if draw_boundaries:
        vec_length = 3000
        pyglet.shapes.Line(point1[0], point1[1], point1[0]+vec_length*v1[0], point1[1]+vec_length*v1[1], width=5, color=[200, 200, 100]).draw()
        pyglet.shapes.Line(point1[0], point1[1], point1[0]+vec_length*v2[0], point1[1]+vec_length*v2[1], width=5, color=[200, 200, 100]).draw()
        pyglet.shapes.Line(point2[0], point2[1], point2[0]+vec_length*v3[0], point2[1]+vec_length*v3[1], width=5, color=[200, 200, 100]).draw()
        pyglet.shapes.Line(point2[0], point2[1], point2[0]+vec_length*v4[0], point2[1]+vec_length*v4[1], width=5, color=[200, 200, 100]).draw()

    if draw_background:
        background.draw()
    lines = list()
    #flocks = list()
    for boid in boids:
        boid.draw()

        if DRAW_PRIMITIVES:
            """xmax, ymax = game_window.width, game_window.height
            intersections = []
            corners = {'p1': ([0, 0], [1, 0], [0, 1]),
                       'p2': ([0, ymax], [0, -1], [1, 0]),
                       'p3': ([xmax, ymax], [-1, 0], [0, -1]),
                       'p4': ([xmax, 0], [-1, 0], [0, 1])}

            quad = (boid.rotation // 90) % 4 + 1
            if quad == 1:
                p, vector1, vector2 = corners['p3']
            if quad == 2:
                p, vector1, vector2 = corners['p2']
            if quad == 3:
                p, vector1, vector2 = corners['p1']
            if quad == 4:
                p, vector1, vector2 = corners['p4']
            vectors = [vector1, vector2]

            pyglet.shapes.Circle(p[0], p[1], 50).draw()
            pyglet.shapes.Line(p[0], p[1], p[0]+60*vector1[0], p[1]+60*vector1[1], color=[100,0,100],width=15).draw()
            pyglet.shapes.Line(p[0], p[1], p[0] + 60 * vector2[0], p[1] + 60 * vector2[1], color=[100,0,100],width=15).draw()
            for vector in vectors:
                v = vector
                intersection = boid.get_intersection(p, v)
                if intersection:
                    intersections.append(intersection)
            #for intersection in intersections:
            #    pyglet.shapes.Line(boid.x, boid.y, intersection[0], intersection[1]).draw()
            """

            rot = math.radians(boid.rotation)
            pyglet.shapes.Line(boid.x, boid.y, boid.x + 60 * math.cos(rot), (boid.y + 60 * math.sin(rot))).draw()
            pyglet.shapes.Line(boid.x, boid.y, boid.x + 300 * math.cos(rot), (boid.y + 300 * math.sin(rot)),
                               color=[255, 100, 100]).draw()
            pyglet.shapes.Line(boid.x, boid.y, boid.x + 150 * math.cos(rot), (boid.y + 150 * math.sin(rot)),
                               color=[100, 50, 25]).draw()

        other_boids = boids.copy()
        other_boids.remove(boid)
        closest_boid, distance, other_close_boids = boid.find_closest(other_boids)
        if distance < 200 and DRAW_PRIMITIVES and RULES['align'] and boid and closest_boid:
            lines.append(pyglet.shapes.Line(boid.x, boid.y, closest_boid.x, closest_boid.y, color=(150, 20, 90)))

    for line in lines:
        line.draw()
    for message in MESSAGES:
        message.draw()


def update(dt):
    other_close_boids = list()
    for shot in shots:
        shot.update(dt)
    for boid in boids:
        boid_killed = False
        if RULES['hunt_player']:
            for shot in shots:
                if math.dist(shot.position, boid.position) < 20 and not boid is PLAYER:
                    if boid in boids:
                        hit_sound.play()
                        boids.remove(boid)
                        boid_killed = True
                    if shot in shots:
                        shots.remove(shot)
        if boid_killed:
            break

        #centers = dict()
        #new_flocks = list()
        #for flock in new_flocks:
        #    print(flock)
        #    for boid in flock.boids_in_flock:
        #        centers[boid] = flock.calculate_center()
        other_boids = boids.copy()
        other_boids.remove(boid)
        if other_boids:
            closest_boid, distance, other_close_boids = boid.find_closest(other_boids)
            #center = centers[boid] if boid in centers else None
        else:
            closest_boid, center = None, None
        center = None
        if other_close_boids:
            other_close_boids.append(closest_boid)
            #centerx = (sum([close_boid.x for close_boid in other_close_boids])+boid.x)/(len(other_close_boids)+1)
            #centery = (sum([close_boid.y for close_boid in other_close_boids])+boid.y)/(len(other_close_boids)+1)
            #center = [centerx, centery]
        if center:
            CENTERS[boid] = center
        boid.update(closest_boid=closest_boid, center=center, game_window=game_window, rules=RULES, dt=dt, player=PLAYER) if boid else None
    if PLAYER:
        global PLAYER_CREATED
        if PLAYER.check_death() and PLAYER_CREATED:
            MESSAGES.append(pyglet.text.Label(f'Player killed',
                                              x=game_window.width//2, y=game_window.height//2,
                                              font_size=font_size, color=color))
            death_sound.play()
            RULES['hunt_player'] = False
            PLAYER_CREATED = False
            boids.remove(PLAYER)




@game_window.event
def on_key_press(symbol, modifiers):
    global PLAYER
    global PLAYER_CREATED

    if symbol == pyglet.window.key.N:
        new_boid = BoidShape(0, 0, radius)
        new_boid.x, new_boid.y = game_window.width//2, game_window.height//2
        new_boid.smart = random.choice([False, True])
        boids.append(new_boid)

    if symbol == pyglet.window.key.M:
        last_boid = boids[-1] if boids else None
        if last_boid:
            boids.pop()
            if type(last_boid) == PlayerBoid:
                PLAYER = None
                PLAYER_CREATED = False
            del last_boid

    if symbol == pyglet.window.key.SPACE:
        global DRAW_PRIMITIVES
        DRAW_PRIMITIVES = False if DRAW_PRIMITIVES else True

    if symbol == pyglet.window.key.A:
        rules_message('handle_collision', MESSAGES, RULES, game_window, font_size, color)

    if symbol == pyglet.window.key.S:
        rules_message('align', MESSAGES, RULES, game_window, font_size, color)

    if symbol == pyglet.window.key.D:
        rules_message('navigate_toward_center', MESSAGES, RULES, game_window, font_size, color)
    if symbol == pyglet.window.key.F and PLAYER:
        rules_message('hunt_player', MESSAGES, RULES, game_window, font_size, color)

    if symbol == pyglet.window.key.P:
        global PLAYABLE
        PLAYABLE = True
        if PLAYABLE and not PLAYER_CREATED:
            PLAYER = PlayerBoid(20, 20, radius + 2, color=color[0:3])
            PLAYER.position = [game_window.width // 2, game_window.height // 2]
            game_window.push_handlers(PLAYER.key_handler)
            boids.append(PLAYER)
            PLAYER_CREATED = True
            player_sound.play()

    if symbol == pyglet.window.key.T:
        if PLAYER_CREATED:
            shot_sound.play()
            shot = Shot(x=PLAYER.x, y=PLAYER.y, radius=radius-2)
            shot.color = [150, 50, 50]
            shot.rotation = PLAYER.rotation
            shot.velocity = abs(PLAYER.velocity) + 500
            shots.append(shot)


@game_window.event
def on_key_release(symbol, modifiers):
    if MESSAGES:
        MESSAGES.pop()


if __name__ == '__main__':
    pyglet.clock.schedule_interval(update, 1 / 120.0)
    pyglet.app.run()