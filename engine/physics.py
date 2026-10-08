import random
from core.config import (
    SIZE, WIN32_AVAILABLE,
    SURFACE_FLOOR, SURFACE_WALL_L, SURFACE_WALL_R, SURFACE_CEILING
)
from core.xml_parser import (
    STAND_FRAMES, WALK_FRAMES, WALK_BACK, SIT_FRAMES,
    GUITAR_FRAMES, LIE_FRAMES, BLOB_FRAMES, GHOST_FRAMES,
    BOX_FRAMES, FALL_FRAMES, KNEEL_FRAMES, CARRY_FRAMES,
    DEPRESS_FRAMES, AWAY_FRAMES, CLIMB_FRAMES, is_standard_shimeji
)

if WIN32_AVAILABLE:
    import win32gui
    import win32api
    import win32con


class MascotPhysics:
    """
    Kinematics and environment physics engine for Alastor Shimeji mascot.
    Handles screen boundaries, wall climbing, ceiling walking, cursor following,
    and dynamic platform walking on active application windows and browser tabs.
    """
    WALK_SPEED  = 2
    FALL_SPEED  = 8
    CLIMB_SPEED = 2

    def __init__(self, screen_w: int, screen_h: int, surface_detector=None):
        self.sw = screen_w
        self.sh = screen_h
        self.surface_detector = surface_detector

        self.ground_y  = self.sh - SIZE - 40
        self.ceiling_y = 0
        self.wall_lx   = 0
        self.wall_rx   = self.sw - SIZE

        self.x = float(random.randint(self.wall_lx + 100, max(self.wall_lx + 100, self.wall_rx - 100)))
        self.y = float(self.ground_y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.gravity = 0

        self.surface = SURFACE_FLOOR
        self.state   = "standing"
        self.flipped = False
        self.rotation = 0

        self.current_anim = STAND_FRAMES
        self.frame_idx    = 0
        self.frame_timer  = 0
        self.frame_delay  = 4

        # Window platform walking attributes
        self.target_window_hwnd = 0
        self.walk_on_windows_enabled = True
        self.current_floor_y = self.ground_y
        self.current_floor_min_x = self.wall_lx
        self.current_floor_max_x = self.wall_rx
        self.follow_cursor_enabled = False

    def set_state(self, state: str, surface: str = None):
        self.state       = state
        self.frame_idx   = 0
        self.frame_timer = 0
        if surface:
            self.surface = surface

        anim_map = {
            "standing":     STAND_FRAMES,
            "walking":      WALK_FRAMES,
            "walk_back":    WALK_BACK,
            "sitting":      SIT_FRAMES,
            "guitar":       GUITAR_FRAMES,
            "lie":          LIE_FRAMES,
            "blob":         BLOB_FRAMES,
            "ghost":        GHOST_FRAMES,
            "box":          BOX_FRAMES,
            "falling":      FALL_FRAMES,
            "kneel":        KNEEL_FRAMES,
            "carry":        CARRY_FRAMES,
            "depress":      DEPRESS_FRAMES,
            "away":         AWAY_FRAMES,
            "climb_left":   CLIMB_FRAMES,
            "climb_right":  CLIMB_FRAMES,
            "ceiling_walk": WALK_FRAMES,
            "ceiling_idle": STAND_FRAMES,
        }
        self.current_anim = anim_map.get(state, STAND_FRAMES)
        if not self.current_anim:
            self.current_anim = STAND_FRAMES

        if state == "walking":
            self.vel_x = random.choice([-1, 1]) * self.WALK_SPEED
            self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)
            self.rotation = 0
        elif state == "walk_back":
            self.vel_x = -self.vel_x if self.vel_x != 0 else self.WALK_SPEED
            self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)
            self.rotation = 0
        elif state == "climb_left":
            self.vel_x = 0
            if self.vel_y == 0:
                self.vel_y = -self.CLIMB_SPEED
            self.rotation = 0
            self.flipped = False
        elif state == "climb_right":
            self.vel_x = 0
            if self.vel_y == 0:
                self.vel_y = -self.CLIMB_SPEED
            self.rotation = 0
            self.flipped = True
        elif state == "ceiling_walk":
            if self.vel_x == 0:
                self.vel_x = random.choice([-1, 1]) * self.WALK_SPEED
            self.flipped = (self.vel_x < 0) if is_standard_shimeji else (self.vel_x > 0)
            self.rotation = 180
        elif state == "ceiling_idle":
            self.vel_x = 0
            self.vel_y = 0
            self.rotation = 180
        elif state == "falling":
            self.rotation = 0
        else:
            self.vel_x = 0
            self.vel_y = 0
            self.rotation = 0

    def choose_next_floor_state(self):
        pool = (["walking"] * 15 +
                ["standing"] * 2 + ["guitar"] * 1 +
                ["blob"] * 1 + ["ghost"] * 1 + ["box"] * 1 +
                ["sitting"] * 1)
        self.set_state(random.choice(pool), surface=SURFACE_FLOOR)

    def choose_next_ceiling_state(self):
        if random.random() < 0.8:
            self.set_state("ceiling_walk", surface=SURFACE_CEILING)
            self.vel_x = random.choice([-1, 1]) * self.WALK_SPEED
            self.flipped = (self.vel_x < 0) if is_standard_shimeji else (self.vel_x > 0)
            self.vel_y = 0
        else:
            self.set_state("ceiling_idle", surface=SURFACE_CEILING)
            self.vel_x = 0
            self.vel_y = 0

    def update_physics(self):
        if self.follow_cursor_enabled and WIN32_AVAILABLE:
            self._move_towards_cursor()

        if self.state == "falling":
            self.gravity = min(self.gravity + 1, 20)
            self.y      += self.gravity
            self.x      += self.vel_x

            # Check if we can land on an open window platform
            if self.walk_on_windows_enabled and WIN32_AVAILABLE and self.surface_detector:
                landing_win = self.surface_detector.find_surface_landing(self.x, self.y)
                if landing_win and self.y >= landing_win["floor_y"] and self.y < self.ground_y - 25:
                    self.target_window_hwnd = landing_win["hwnd"]
                    self.current_floor_y = landing_win["floor_y"]
                    self.current_floor_min_x = landing_win["min_x"]
                    self.current_floor_max_x = landing_win["max_x"]
                    self.y = self.current_floor_y
                    self.gravity = 0
                    self.set_state("standing", SURFACE_FLOOR)
                    return

            # Check ground floor
            if self.y >= self.ground_y:
                self.y = self.ground_y
                self.gravity = 0
                self.target_window_hwnd = 0
                self.current_floor_y = self.ground_y
                self.current_floor_min_x = self.wall_lx
                self.current_floor_max_x = self.wall_rx
                self.set_state("standing", SURFACE_FLOOR)
            return

        if self.surface == SURFACE_FLOOR and self.y < self.current_floor_y:
            self.set_state("falling", SURFACE_FLOOR)
            return

        if self.surface == SURFACE_FLOOR:
            self._physics_floor()
        elif self.surface in (SURFACE_WALL_L, SURFACE_WALL_R):
            self._physics_wall()
        elif self.surface == SURFACE_CEILING:
            self._physics_ceiling()

    def _move_towards_cursor(self):
        try:
            cursor_x, cursor_y = win32api.GetCursorPos()
            center_x = self.x + SIZE // 2
            center_y = self.y + SIZE // 2

            dx = cursor_x - center_x
            dy = cursor_y - center_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance > 80:
                self.vel_x = (dx / distance) * (self.WALK_SPEED * 1.5)
                self.x += self.vel_x
                self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)
                if self.state != "walking":
                    self.set_state("walking", surface=SURFACE_FLOOR)
            else:
                self.vel_x = 0
                if self.state == "walking":
                    self.set_state("standing", surface=SURFACE_FLOOR)
        except Exception:
            pass

    def _physics_floor(self):
        # If on a window, track its movement
        if self.target_window_hwnd and WIN32_AVAILABLE:
            try:
                if (win32gui.IsWindow(self.target_window_hwnd) and
                        win32gui.IsWindowVisible(self.target_window_hwnd) and
                        not win32gui.IsIconic(self.target_window_hwnd)):
                    rect = win32gui.GetWindowRect(self.target_window_hwnd)
                    self.current_floor_y = rect[1] - SIZE + 15
                    self.current_floor_min_x = rect[0]
                    self.current_floor_max_x = rect[2] - SIZE
                    self.y = self.current_floor_y
                else:
                    self.target_window_hwnd = 0
                    self.current_floor_y = self.ground_y
                    self.current_floor_min_x = self.wall_lx
                    self.current_floor_max_x = self.wall_rx
                    self.set_state("falling", surface=SURFACE_FLOOR)
                    return
            except Exception:
                self.target_window_hwnd = 0
                self.current_floor_y = self.ground_y
        else:
            self.y = self.ground_y
            self.current_floor_y = self.ground_y
            self.current_floor_min_x = self.wall_lx
            self.current_floor_max_x = self.wall_rx

        self.x += self.vel_x

        # Left edge
        if self.x <= self.current_floor_min_x:
            self.x = self.current_floor_min_x
            if self.target_window_hwnd:
                if random.random() < 0.25:
                    self.target_window_hwnd = 0
                    self.set_state("falling", surface=SURFACE_FLOOR)
                    self.vel_x = -2
                    return
                else:
                    self.vel_x = abs(self.vel_x)
                    self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)
            else:
                if random.random() < 0.4:
                    self.start_climb(SURFACE_WALL_L, going_up=True)
                else:
                    self.vel_x = abs(self.vel_x)
                    self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)

        # Right edge
        elif self.x >= self.current_floor_max_x:
            self.x = self.current_floor_max_x
            if self.target_window_hwnd:
                if random.random() < 0.25:
                    self.target_window_hwnd = 0
                    self.set_state("falling", surface=SURFACE_FLOOR)
                    self.vel_x = 2
                    return
                else:
                    self.vel_x = -abs(self.vel_x)
                    self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)
            else:
                if random.random() < 0.4:
                    self.start_climb(SURFACE_WALL_R, going_up=True)
                else:
                    self.vel_x = -abs(self.vel_x)
                    self.flipped = (self.vel_x > 0) if is_standard_shimeji else (self.vel_x < 0)

    def _physics_wall(self):
        self.y += self.vel_y
        if self.vel_y < 0 and self.y <= self.ceiling_y:
            self.y = self.ceiling_y
            if random.random() < 0.6:
                self.surface = SURFACE_CEILING
                self.choose_next_ceiling_state()
            else:
                self.set_state("falling", surface=SURFACE_FLOOR)
                self.vel_x = 3 if self.surface == SURFACE_WALL_L else -3
        elif self.vel_y > 0 and self.y >= self.ground_y:
            self.y = self.ground_y
            self.surface = SURFACE_FLOOR
            self.choose_next_floor_state()

    def _physics_ceiling(self):
        self.y = self.ceiling_y
        self.x += self.vel_x
        if self.x <= self.wall_lx:
            self.x = self.wall_lx
            r = random.random()
            if r < 0.4:
                self.start_climb(SURFACE_WALL_L, going_up=False)
            elif r < 0.7:
                self.vel_x = abs(self.vel_x)
                self.flipped = (self.vel_x < 0) if is_standard_shimeji else (self.vel_x > 0)
            else:
                self.set_state("falling", surface=SURFACE_FLOOR)
        elif self.x >= self.wall_rx:
            self.x = self.wall_rx
            r = random.random()
            if r < 0.4:
                self.start_climb(SURFACE_WALL_R, going_up=False)
            elif r < 0.7:
                self.vel_x = -abs(self.vel_x)
                self.flipped = (self.vel_x < 0) if is_standard_shimeji else (self.vel_x > 0)
            else:
                self.set_state("falling", surface=SURFACE_FLOOR)

    def start_climb(self, wall: str, going_up: bool = True):
        self.surface = wall
        spd = -self.CLIMB_SPEED if going_up else self.CLIMB_SPEED
        self.vel_x = 0
        if wall == SURFACE_WALL_L:
            self.x = self.wall_lx
            self.set_state("climb_left")
        else:
            self.x = self.wall_rx
            self.set_state("climb_right")
        self.vel_y = spd

    def force_climb(self, wall: str):
        if wall == SURFACE_WALL_L:
            self.x = self.wall_lx
        else:
            self.x = self.wall_rx
        self.y = self.ground_y
        self.start_climb(wall, going_up=True)

    def force_ceiling(self):
        self.y = self.ceiling_y
        self.x = max(self.wall_lx, min(self.x, self.wall_rx))
        self.choose_next_ceiling_state()

    def jump_to_window(self, target: dict) -> bool:
        if not target:
            return False
        self.target_window_hwnd = target["hwnd"]
        self.current_floor_y = target["floor_y"]
        self.current_floor_min_x = target["min_x"]
        self.current_floor_max_x = target["max_x"]

        center_x = (target["left"] + target["right"]) // 2 - SIZE // 2
        self.x = max(self.current_floor_min_x, min(center_x, self.current_floor_max_x))
        self.y = self.current_floor_y
        self.gravity = 0
        self.set_state("walking", surface=SURFACE_FLOOR)
        return True

    def jump_to_floor(self) -> bool:
        if self.target_window_hwnd != 0 or self.y < self.ground_y:
            self.target_window_hwnd = 0
            self.current_floor_y = self.ground_y
            self.current_floor_min_x = self.wall_lx
            self.current_floor_max_x = self.wall_rx
            self.set_state("falling", surface=SURFACE_FLOOR)
            self.vel_x = random.choice([-2, 2])
            return True
        return False
