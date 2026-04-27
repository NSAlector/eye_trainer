import math

def calc_cur_coordinates_circle_right(current_time, orbit_radius, ground_sz, orbit_speed=1.0):
    angle = current_time * orbit_speed
    #x = center + radius * cos(time) y = center + radius * sin(time)
    x = orbit_radius * math.cos(angle)
    z = orbit_radius * math.sin(angle)
    y = 0.5  
    
    return x, y, z

def calc_cur_coordinates_circle_left(current_time, orbit_radius, ground_sz, orbit_speed=1.0):
    angle = current_time * orbit_speed
    #x = center + radius * cos(time) y = center + radius * sin(time)
    x = orbit_radius * math.cos(angle)
    z = orbit_radius * math.sin(angle)
    y = 0.5  
    
    return -x, y, z

#от парвый верхний в левого нижнего
def calc_cur_coordinates_diagonal_down(current_time, orbit_radius, ground_sz, speed=1.0):
    angle = current_time * speed
    val =  math.sin(angle) * (ground_sz/2)
    y = 0.5
    
    return val, y, val


#от левого нижнего в парвый верхний не сдвигом фазы, а просто -
def calc_cur_coordinates_diagonal_up(current_time, orbit_radius, ground_sz, speed=1.0):
    angle = current_time * speed
    val =  math.sin(angle) * (ground_sz/2)
    y = 0.5
    return -val, y, val

def calc_cur_coordinates_hotizontal(current_time, orbit_radius, ground_sz, speed=1.0):
    angle = current_time * speed
    z = math.sin(angle)*ground_sz
    y = 0.5
    x = 0
    
    return x, y, z

def calc_cur_coordinates_vertical(current_time, orbit_radius, ground_sz,  speed=1.0):
    angle = current_time * speed
    x = math.sin(angle)*ground_sz
    y = 0.5
    z = 0
    
    return x, y, z

def calc_cur_coordinates_zigzag(current_time, orbit_radius, ground_sz, speed):
    y = 0.5
    t = current_time * speed /3

    # период зиг-зага (вперёд + назад)
    period = 1.0
    phase = (t % period) / period  # 0..1

    # пилообразная форма: 0→1→0→1→…
    saw = 2 * abs(phase - 0.5)

    # движение от -ground_sz/2 до +ground_sz/2 и обратно
    z = (saw - 0.5) * ground_sz

    x = orbit_radius * math.sin(t)

    return x, y, z

def calc_cur_coordinates_clock(current_time, orbit_radius, ground_sz, speed):
    y = 0.5
    #вариант с автоматом или с парсированием врмемени
    MOVE_TIME = 2.0
    STOP_TIME = 1.0
    CYCLE_TIME = 12.0
    
    t = current_time * speed
    cycle_time = t % CYCLE_TIME
    
    if cycle_time < MOVE_TIME:
        #  1: Движение от 9 к 12 часам
        progress = cycle_time / MOVE_TIME
        angle = math.pi + progress * (math.pi/2)  # π → 3π/2
        
    elif cycle_time < MOVE_TIME + STOP_TIME:
        #  2: Остановка на 12 часах
        angle = 3 * math.pi / 2  # 270°
        
    elif cycle_time < 2*MOVE_TIME + STOP_TIME:
        #  3: Движение от 12 к 3 часам
        segment_time = cycle_time - (MOVE_TIME + STOP_TIME)
        progress = segment_time / MOVE_TIME
        angle = 3*math.pi/2 + progress * (math.pi/2)  # 3π/2 → 2π (0)
        
    elif cycle_time < 2*MOVE_TIME + 2*STOP_TIME:
        #  4: Остановка на 3 часах
        angle = 0  # 0°
        
    elif cycle_time < 3*MOVE_TIME + 2*STOP_TIME:
        #  5: Движение от 3 к 6 часам
        segment_time = cycle_time - (2*MOVE_TIME + 2*STOP_TIME)
        progress = segment_time / MOVE_TIME
        angle = 0 + progress * (math.pi/2)  # 0 → π/2
        
    elif cycle_time < 3*MOVE_TIME + 3*STOP_TIME:
        #  6: Остановка на 6 часах
        angle = math.pi / 2  # 90°
        
    elif cycle_time < 4*MOVE_TIME + 3*STOP_TIME:
        #  7: Движение от 6 к 9 часам
        # Движение: по часовой стрелке на 90°
        segment_time = cycle_time - (3*MOVE_TIME + 3*STOP_TIME)
        progress = segment_time / MOVE_TIME
        angle = math.pi/2 + progress * (math.pi/2)  # π/2 → π
        
    else:
        #  8: Остановка на 9 часах
        angle = math.pi  # 180°
    
    #угол в диапазон 0-2π
    angle = angle % (2 * math.pi)
    
    x = orbit_radius * math.cos(angle)
    z = orbit_radius * math.sin(angle)
    
    return x, y, z

def calc_cur_coordinates_two_diagonals(current_time, orbit_radius, ground_sz, speed):
    y = 0.5
    t = current_time
    
    #цикл по 12 секунд, по 6 на сторону
    period_num = int(t) % 12
    
    angle = t * math.pi 
    val = math.sin(angle) * (ground_sz/2)
    
    if period_num < 6:
        return -val, y, val
    else:
        return val, y, val


def calc_cur_coordinates_rectangle(current_time, orbit_radius, ground_sz, speed):
    side_duration=5.0
    width_factor=2/3
    y = 0.5
    t = current_time * speed
    half_size = width_factor * ground_sz
    full_size = 2 * half_size

    cycle_duration = 4 * side_duration
    cycle_time = t % cycle_duration
        
    if cycle_time < side_duration:
        #правый край, сверху вниз
        progress = cycle_time / side_duration
        x = half_size
        z = half_size - progress * full_size
            
    elif cycle_time < 2 * side_duration:
        #нижний край, справа налево
        progress = (cycle_time - side_duration) / side_duration
        z = -half_size
        x = half_size - progress * full_size
            
    elif cycle_time < 3 * side_duration:
        #левый край, снизу вверх
        progress = (cycle_time - 2 * side_duration) / side_duration
        x = -half_size
        z = -half_size + progress * full_size
            
    else:
        #верхний край, слева направо
        progress = (cycle_time - 3 * side_duration) / side_duration
        z = half_size
        x = -half_size + progress * full_size
        
    return x, y, z

movements = {
    "circle_right": calc_cur_coordinates_circle_right,
    "circle_left": calc_cur_coordinates_circle_left,
    "diagonal_up": calc_cur_coordinates_diagonal_up,
    "diagonal_down": calc_cur_coordinates_diagonal_down,
    "horizontal": calc_cur_coordinates_hotizontal,
    "vertical": calc_cur_coordinates_vertical,
    "zigzag": calc_cur_coordinates_zigzag,
    "clock": calc_cur_coordinates_clock,
    "two_diagonals": calc_cur_coordinates_two_diagonals,
    "rectangle": calc_cur_coordinates_rectangle,
}

