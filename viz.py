import pygame
import math

LOGFILE = 'log.txt'

# We have a robot that moves in a 2D arena of size 3x3m with 12x12 squares
# Parse the log file and visualize the robot's trajectory in pygame

ARENA_SIZE = 3.0
ARENA_SCREEN_SIZE = 800
SIDEBAR_WIDTH = 600
N_CELLS = 12
PIXELS_PER_METER = ARENA_SCREEN_SIZE / ARENA_SIZE

WALL_THICKNESS = 3

SHRINK_TIME = 20.0

states = []
state = None
with open(LOGFILE, 'r') as f:
    for line in f.read().splitlines()[:-5]: # Get rid of the end of the file (in case of corrupted logs)
        if '{State};' in line:
            if state is not None:
                states.append(state)
            time_ms, logger_id, timeUntilShrink = line.split('{State};')[1].strip(';').split(';')
            state = {
                'time_ms': int(time_ms),
                'time_until_shrink': float(timeUntilShrink),
                'robots': [],
                'grid': [[None for _ in range(N_CELLS)] for _ in range(N_CELLS)],
                'log_lines': [],
                'logger_id': int(logger_id),
                'draw_lines': [],
                'draw_points': [],
                'bomb_data': {}
            }
        elif '{Robot_' in line:
            robot_id = int(line.split('{Robot_')[1].split('}')[0])
            if robot_id == 0:
                continue # Not connected
            x, y, a, speed_limit, team, is_live, score, inventory = line.split('}')[1].strip(';').split(';')
            robot = {
                'id': int(robot_id),
                'x': float(x),
                'y': float(y),
                'a': float(a),
                'speed_limit': float(speed_limit),
                'team': int(team),
                'is_live': int(is_live),
                'score': int(score),
                'inventory': int(inventory)
            }
            state['robots'].append(robot)
        elif '{Grid};' in line:
            gridsize, _ = line.split('{Grid};')[1].split(';')
            state['gridsize'] = float(gridsize)
        elif '{Maze_' in line:
            maze_i = int(line.split('{Maze_')[1].split('}')[0])
            assert 0 <= maze_i < N_CELLS
            cells_bits = line.split('}')[1].strip(';').split(';')
            assert len(cells_bits) == N_CELLS, line
            for j, cell_bits in enumerate(cells_bits):
                bitmap = int(cell_bits)
                coin_value = bitmap & 0b111
                danger_value = (bitmap >> 3) & 0b111
                north_wall = not ((bitmap >> 6) & 1)
                west_wall = not ((bitmap >> 7) & 1)
                south_wall = not ((bitmap >> 8) & 1)
                east_wall = not ((bitmap >> 9) & 1)
                possession1 = (bitmap >> 10) & 1
                possession2 = (bitmap >> 11) & 1
                is_bomb = (bitmap >> 12) & 1
                cell = {
                    'coin_value': coin_value,
                    'danger_value': danger_value,
                    'north_wall': north_wall,
                    'west_wall': west_wall,
                    'south_wall': south_wall,
                    'east_wall': east_wall,
                    'possession1': possession1,
                    'possession2': possession2,
                    'is_bomb': is_bomb,
                    'bomb_data': None
                }
                assert state['grid'][maze_i][j] is None
                state['grid'][maze_i][j] = cell
        elif '{Bomb_' in line:
            bomb_i, bomb_j = map(int, line.split('{Bomb_')[1].split('}')[0].split('_'))
            assert 0 <= bomb_i < N_CELLS
            assert 0 <= bomb_j < N_CELLS
            bomb_owner, bomb_timer = line.split('}')[1].strip(';').split(';')
            #assert state['grid'][bomb_i][bomb_j]['is_bomb']
            state['grid'][bomb_i][bomb_j]['is_bomb'] = True
            assert state['grid'][bomb_i][bomb_j]['bomb_data'] is None
            state['grid'][bomb_i][bomb_j]['bomb_data'] = (int(bomb_owner), float(bomb_timer))
        elif '{drawLineXY}' in line:
            linedata = line.split('{drawLineXY};')[1].strip(';').split(';')
            color = '#ffffff'
            thickness = 1
            if len(linedata) == 4:
                x1, y1, x2, y2 = linedata
            elif len(linedata) == 5:
                x1, y1, x2, y2, color = linedata
            elif len(linedata) == 6:
                x1, y1, x2, y2, color, thickness = linedata
            state['draw_lines'].append((float(x1), float(y1), float(x2), float(y2), color, int(thickness)))
        elif '{drawLineIJ}' in line:
            linedata = line.split('{drawLineIJ};')[1].strip(';').split(';')
            color = '#ffffff'
            thickness = 1
            if len(linedata) == 4:
                i1, j1, i2, j2 = linedata
            elif len(linedata) == 5:
                i1, j1, i2, j2, color = linedata
            elif len(linedata) == 6:
                i1, j1, i2, j2, color, thickness = linedata
            x1 = int(i1) * ARENA_SIZE / N_CELLS
            y1 = int(j1) * ARENA_SIZE / N_CELLS
            x2 = int(i2) * ARENA_SIZE / N_CELLS
            y2 = int(j2) * ARENA_SIZE / N_CELLS
            state['draw_lines'].append((float(x1), float(y1), float(x2), float(y2), color, int(thickness)))
        elif '{drawPointXY}' in line:
            pointdata = line.split('{drawPointXY};')[1].strip(';').split(';')
            color = '#ffffff'
            thickness = 1
            if len(pointdata) == 2:
                x, y = pointdata
            elif len(pointdata) == 3:
                x, y, color = pointdata
            elif len(pointdata) == 4:
                x, y, color, thickness = pointdata
            state['draw_points'].append((float(x), float(y), color, int(thickness)))
        elif '{drawPointIJ}' in line:
            pointdata = line.split('{drawPointIJ};')[1].strip(';').split(';')
            color = '#ffffff'
            thickness = 1
            if len(pointdata) == 2:
                i, j = pointdata
            elif len(pointdata) == 3:
                i, j, color = pointdata
            elif len(pointdata) == 4:
                i, j, color, thickness = pointdata
            x = int(i) * ARENA_SIZE / N_CELLS
            y = int(j) * ARENA_SIZE / N_CELLS
            state['draw_points'].append((float(x), float(y), color, int(thickness)))
        else:
            if state is not None and ' | ' in line:
                state['log_lines'].append(line.split(' | ', 1)[1])

# Last state is probably corrupted if the logger was deleted, so states.append(state) is omitted here

print(f'Loaded {len(states)} turn states')

def draw_state(screen, state):
    grid_size = state['gridsize']
    cell_size = ARENA_SCREEN_SIZE / N_CELLS
    for col in range(N_CELLS):
        for row in range(N_CELLS):
            cell = state['grid'][row][col]
            if cell is None:
                continue
            # 0, 0 is southwest corner
            x = row * cell_size
            y = (N_CELLS - 1 - col) * cell_size
            cell_text = '' # Can use this to write debug text on the cell
            # Draw possession on the background of the cell. Team 1 is yellow, 2 is blue
            
            active_rc_low = N_CELLS // 2 - grid_size // 2
            active_rc_high = active_rc_low + grid_size

            cell_color = (0, 0, 0)
            if cell['possession1']:
                assert not cell['possession2']
                cell_color = (100, 100, 0)
            elif cell['possession2']:
                assert not cell['possession1']
                cell_color = (0, 0, 150)
            else:
                cell_color = (0, 20, 40)

            if not (active_rc_low <= row < active_rc_high and active_rc_low <= col < active_rc_high):
                cell_color = tuple(comp//2 for comp in cell_color)
            
            pygame.draw.rect(screen, cell_color, (x, y, cell_size+1, cell_size+1))

            # Draw walls as thick lines
            if cell['north_wall']:
                pygame.draw.line(screen, (255, 255, 255), (x, y + WALL_THICKNESS//2), (x + cell_size, y + WALL_THICKNESS//2), WALL_THICKNESS)
            if cell['west_wall']:
                pygame.draw.line(screen, (255, 255, 255), (x + WALL_THICKNESS//2, y), (x + WALL_THICKNESS//2, y + cell_size), WALL_THICKNESS)
            if cell['south_wall']:
                pygame.draw.line(screen, (255, 255, 255), (x, y + cell_size - WALL_THICKNESS//2), (x + cell_size, y + cell_size - WALL_THICKNESS//2), WALL_THICKNESS)
            if cell['east_wall']:
                pygame.draw.line(screen, (255, 255, 255), (x + cell_size - WALL_THICKNESS//2, y), (x + cell_size - WALL_THICKNESS//2, y + cell_size), WALL_THICKNESS)


            # Draw coins and bombs
            if cell['coin_value'] > 0:
                """
                font = pygame.font.Font(None, 24)
                text = font.render(str(cell['coin_value']), True, (255, 255, 255))
                screen.blit(text, (x + 5, y + 5))
                """
                #Draw one small circle per coin
                for i in range(cell['coin_value']):
                    pygame.draw.circle(screen, (255, 255, 0), (x + 10 + i * 15, y + 10), 5)
            
            if cell['is_bomb']:
                pygame.draw.circle(screen, (255, 60, 60), (x + cell_size // 2, y + cell_size // 2), 10)
                if cell['bomb_data'] is not None:
                    bomb_owner, _ = cell['bomb_data']
                    # Draw a small circle in the middle of the bomb with the color of the owner
                    if bomb_owner == 1:
                        pygame.draw.circle(screen, (200, 200, 0), (x + cell_size // 2, y + cell_size // 2), 5)
                    else:
                        assert bomb_owner == 2
                        pygame.draw.circle(screen, (0, 0, 200), (x + cell_size // 2, y + cell_size // 2), 5)
                else:
                    # Draw a small circle in the middle of the bomb with the color of the owner
                    pygame.draw.circle(screen, (200, 200, 200), (x + cell_size // 2, y + cell_size // 2), 5)
            
            # Draw danger value as a border getting thicker
            danger_value = cell['danger_value'] # 0 to 7
            if danger_value > 0:
                pygame.draw.rect(screen, (255, 60, 60), (x, y, cell_size, cell_size), danger_value + 1)

            # Draw cell text
            font = pygame.font.Font(None, 36)
            text = font.render(cell_text, True, (255, 255, 255))
            screen.blit(text, (x + cell_size // 2 - text.get_width() // 2, y + cell_size // 2 - text.get_height() // 2))

    for robot in state['robots']:
        x_screen = robot['x'] * PIXELS_PER_METER
        y_screen = (ARENA_SIZE - robot['y']) * PIXELS_PER_METER
        # black ring if dead, orange if slow, green if fast
        if not robot['is_live']:
            robot_ring_color = (0, 0, 0)
            robot_ring_thickness = 6
        elif robot['speed_limit'] < 0.5:
            robot_ring_color = (255, 100, 0)
            robot_ring_thickness = 2
        else:
            robot_ring_color = (0, 255, 0)
            robot_ring_thickness = 2
        robot_color = (200, 200, 0) if robot['team'] == 1 else (0, 0, 200)
        pygame.draw.circle(screen, robot_color, (int(x_screen), int(y_screen)), 10)
        pygame.draw.circle(screen, robot_ring_color, (int(x_screen), int(y_screen)), 10, robot_ring_thickness)
        # Draw small line in the direction of the robot
        dx = 10 * (robot['speed_limit'] + 1) * math.cos(robot['a'])
        dy = -10 * (robot['speed_limit'] + 1) * math.sin(robot['a'])
        pygame.draw.line(screen, (255, 255, 255), (int(x_screen), int(y_screen)), (int(x_screen + dx), int(y_screen + dy)), 3)
        if robot['id'] == state['logger_id']:
            # Small red dot in the middle of the robot that is being logged
            pygame.draw.circle(screen, (255, 0, 0), (int(x_screen), int(y_screen)), 2)

    score_1 = 0
    score_2 = 0
    for robot in state['robots']:
        if robot['team'] == 1:
            score_1 += robot['score']
        else:
            assert robot['team'] == 2
            score_2 += robot['score']

    # Draw scores in the sidebar
    font = pygame.font.Font(None, 36)
    score_1_center = (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH // 4, 80)
    score_2_center = (ARENA_SCREEN_SIZE + 3 * SIDEBAR_WIDTH // 4, 80)
    pygame.draw.rect(screen, (200, 200, 0), (score_1_center[0] - 50, score_1_center[1] - 30, 100, 60))
    pygame.draw.rect(screen, (0, 0, 200), (score_2_center[0] - 50, score_2_center[1] - 30, 100, 60))
    text = font.render(str(score_1), True, (0, 0, 0))
    screen.blit(text, (score_1_center[0] - text.get_width() // 2, score_1_center[1] - text.get_height() // 2))
    text = font.render(str(score_2), True, (255, 255, 255))
    screen.blit(text, (score_2_center[0] - text.get_width() // 2, score_2_center[1] - text.get_height() // 2))

    # Draw the robot's estimation on time to shrink, as a decreasing blue bar below score
    time_shrink_fill = state['time_until_shrink'] / SHRINK_TIME
    # Clamp to [0, 1]
    time_shrink_fill = max(0, min(1, time_shrink_fill))
    pygame.draw.rect(screen, (0, 0, 255), (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH // 2 - SIDEBAR_WIDTH // 2 * time_shrink_fill, 120, SIDEBAR_WIDTH * time_shrink_fill, 10))

    # Draw log lines in sidebar
    font = pygame.font.Font(None, 24)
    text_lines = state['log_lines']
    for i, log_line in enumerate(text_lines):
        # TODO pygame doesn't handle multiline text, so they can overflow the sidebar
        text = font.render(log_line, True, (255, 255, 255))
        screen.blit(text, (ARENA_SCREEN_SIZE + 10, 150 + i * 20))

    # Draw logged lines and points
    for x1, y1, x2, y2, color, thickness in state['draw_lines']:
        if 0 <= x1 <= ARENA_SIZE and 0 <= y1 <= ARENA_SIZE and 0 <= x2 <= ARENA_SIZE and 0 <= y2 <= ARENA_SIZE:
            pygame.draw.line(screen, pygame.Color(color), (x1 * PIXELS_PER_METER, (ARENA_SIZE - y1) * PIXELS_PER_METER), (x2 * PIXELS_PER_METER, (ARENA_SIZE - y2) * PIXELS_PER_METER), thickness)
        else:
            print('Line out of bounds:', x1, y1, x2, y2)
    for x, y, color, thickness in state['draw_points']:
        if 0 <= x <= ARENA_SIZE and 0 <= y <= ARENA_SIZE:
            pygame.draw.circle(screen, pygame.Color(color), (x * PIXELS_PER_METER, (ARENA_SIZE - y) * PIXELS_PER_METER), thickness)
        else:
            print('Point out of bounds:', x, y)

    # Show cell tooltip on mouse
    mouse_x, mouse_y = pygame.mouse.get_pos()
    tooltip = None

    # Find the closest robot to the mouse
    closest_robot = None
    closest_robot_dist = 1000000
    for robot in state['robots']:
        x_screen = robot['x'] * PIXELS_PER_METER
        y_screen = (ARENA_SIZE - robot['y']) * PIXELS_PER_METER
        dist = ((x_screen - mouse_x) ** 2 + (y_screen - mouse_y) ** 2) ** 0.5
        if dist < closest_robot_dist:
            closest_robot = robot
            closest_robot_dist = dist
    if closest_robot_dist < 20:
        tooltip = f'Robot {closest_robot["id"]}, Team {closest_robot["team"]}, Score {closest_robot["score"]}, Inventory {closest_robot["inventory"]}'

    if tooltip is None:
        cell_i = int(mouse_x // cell_size)
        cell_j = N_CELLS - 1 - int(mouse_y // cell_size)
        if 0 <= cell_i < N_CELLS and 0 <= cell_j < N_CELLS:
            cell = state['grid'][cell_i][cell_j]
            if cell is not None:
                tooltip = f'i={cell_i}, j={cell_j}, Coins={cell["coin_value"]}, Danger={cell["danger_value"]}'

    if tooltip is not None:
        # Draw black rectangle then tooltip text
        font = pygame.font.Font(None, 24)
        text = font.render(tooltip, True, (255, 255, 255))
        pygame.draw.rect(screen, (0, 0, 0), (mouse_x + 5, mouse_y + 5, text.get_width() + 10, text.get_height() + 10))
        screen.blit(text, (mouse_x + 10, mouse_y + 10))
    
                              

pygame.init()
screen = pygame.display.set_mode((ARENA_SCREEN_SIZE + SIDEBAR_WIDTH, ARENA_SCREEN_SIZE))
pygame.display.set_caption('Viz')
clock = pygame.time.Clock()

running = True
state_i = 0
is_playing = True
while running:
    screen.fill((0, 0, 0))
    # Play/pause via spacebar, move in time with left/right arrows. Single frame step with up/down arrows
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                is_playing = not is_playing
            if event.key == pygame.K_DOWN:
                state_i = max(state_i - 1, 0)
            if event.key == pygame.K_UP:
                state_i = min(state_i + 1, len(states) - 1)
        if event.type == pygame.QUIT:
            running = False

    if keys[pygame.K_LEFT]:
        state_i = max(state_i - 1, 0)
    elif keys[pygame.K_RIGHT]:
        state_i = min(state_i + 1, len(states) - 1)
    elif is_playing:
        state_i = min(state_i + 1, len(states) - 1)

    # Draw state scrollbar and play/pause state
    bar_progress = state_i / len(states)
    pygame.draw.rect(screen, (100, 100, 100), (ARENA_SCREEN_SIZE, 0, SIDEBAR_WIDTH, 10))
    pygame.draw.rect(screen, (200, 200, 200), (ARENA_SCREEN_SIZE, 0, bar_progress * SIDEBAR_WIDTH, 10))
    pygame.draw.rect(screen, (200, 200, 200), (ARENA_SCREEN_SIZE + bar_progress * SIDEBAR_WIDTH, 0, 10, 10))
    pygame.draw.rect(screen, (200, 200, 200), (ARENA_SCREEN_SIZE + bar_progress * SIDEBAR_WIDTH - 10, 0, 10, 10))
    if is_playing:
        pygame.draw.rect(screen, (0, 255, 0), (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH - 20, 20, 10, 10))
        pygame.draw.rect(screen, (0, 255, 0), (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH - 10, 20, 10, 10))
    else:
        pygame.draw.rect(screen, (255, 0, 0), (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH - 20, 20, 10, 10))
        pygame.draw.rect(screen, (255, 0, 0), (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH - 10, 20, 10, 10))
    # Show current state number and total count
    font = pygame.font.Font(None, 30)
    text = font.render(f'{state_i+1}/{len(states)}', True, (255, 255, 255))
    framecnt_center = (ARENA_SCREEN_SIZE + SIDEBAR_WIDTH // 2, 20)
    screen.blit(text, (framecnt_center[0] - text.get_width() // 2, framecnt_center[1] - text.get_height() // 2))

    draw_state(screen, states[state_i])
    pygame.display.flip()
    clock.tick(60) # Cap framerate to 60 FPS

pygame.quit()