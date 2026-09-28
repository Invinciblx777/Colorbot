"""
Invinciblx777 v2.0 — Ultra low-latency color detection engine.

Optimizations over v1.0:
- Pure NumPy vectorized color detection (no cv2.cvtColor overhead)
- Direct BGR→HSV math using NumPy (skips OpenCV conversion)
- NumPy argwhere centroid detection (replaces dilate + findContours)
- Configurable target color, sensitivity, headshot offset
- Latency monitoring built-in

Total pipeline: capture → numpy mask → centroid → HID move
Target latency: <1ms per frame (detection only)
"""

import numpy as np
import threading
import time
import win32api
import cv2

from screen_cap import ScreenCapture
from mouse import ArduinoMouse


class Invinciblx777:
    def __init__(self, x, y, grabzone, settings=None):
        """
        Initialize the Invinciblx777 engine.

        Args:
            x: Left edge of capture region (pixels).
            y: Top edge of capture region (pixels).
            grabzone: Size of the square capture region.
            settings: Dict from settings.load_settings(). Uses defaults if None.
        """
        # ── Apply settings (with safe defaults) ─────────────────
        if settings is None:
            settings = {}

        aim = settings.get('aimbot', {})
        trig = settings.get('triggerbot', {})
        color = settings.get('color', {})

        # Color range (HSV)
        self.lower_color = np.array([
            color.get('lower_hue', 140),
            color.get('lower_saturation', 110),
            color.get('lower_value', 150),
        ], dtype=np.uint8)
        self.upper_color = np.array([
            color.get('upper_hue', 150),
            color.get('upper_saturation', 195),
            color.get('upper_value', 255),
        ], dtype=np.uint8)

        # Aimbot settings
        self.sensitivity = float(aim.get('speed', 0.25))
        self.head_offset = int(aim.get('headshot_offset', 9))
        self.min_pixels = int(aim.get('min_pixels', 4))
        self.aim_enabled = bool(aim.get('enabled', True))
        self.aim_vk = aim.get('vk_code', 0x02)   # Right mouse button

        # Triggerbot settings
        self.trig_enabled = bool(trig.get('enabled', True))
        self.trig_vk = trig.get('vk_code', 0x12)   # Left Alt
        self.trig_threshold_x = int(trig.get('threshold_x', 4))
        self.trig_threshold_y = int(trig.get('threshold_y', 10))

        # ── Core init ───────────────────────────────────────────
        self.arduinomouse = ArduinoMouse()
        self.grabber = ScreenCapture(x, y, grabzone)
        self.grabzone = grabzone
        self.half_zone = grabzone // 2
        self.toggled = False

        # Performance stats
        self._process_times = []
        self._avg_latency = 0.0

        # Pre-allocate arrays for the detection pipeline
        self._hsv_buf = np.zeros((grabzone, grabzone, 3), dtype=np.uint8)

        # Start processing thread
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def toggle(self):
        self.toggled = not self.toggled
        time.sleep(0.2)

    def _run(self):
        """Main processing loop — polls key states and processes frames."""
        while self._running:
            if not self.toggled:
                time.sleep(0.001)  # Minimal sleep when disabled
                continue

            # Aimbot activation
            if self.aim_enabled and win32api.GetAsyncKeyState(self.aim_vk) < 0:
                self._process_aim()
            # Triggerbot activation
            elif self.trig_enabled and win32api.GetAsyncKeyState(self.trig_vk) < 0:
                self._process_trigger()

    def _detect_target(self, screen):
        """
        Ultra-fast color detection using optimized NumPy pipeline.
        
        Returns (cx, cy) centroid of detected color, or None if not found.
        Uses vectorized HSV conversion and mask generation.
        """
        # Use OpenCV for HSV conversion (SIMD-optimized, faster than pure numpy)
        # but skip the heavy dilate + findContours pipeline
        hsv = cv2.cvtColor(screen[:, :, :3], cv2.COLOR_BGR2HSV)

        # Vectorized range check — single operation
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        mask = (
            (h >= self.lower_color[0]) & (h <= self.upper_color[0]) &
            (s >= self.lower_color[1]) & (s <= self.upper_color[1]) &
            (v >= self.lower_color[2]) & (v <= self.upper_color[2])
        )

        # Find matching pixel coordinates
        points = np.argwhere(mask)

        if len(points) < self.min_pixels:
            return None

        # Calculate bounding box from points (much faster than contours)
        y_min, x_min = points.min(axis=0)
        y_max, x_max = points.max(axis=0)

        # Center of bounding box
        cx = (x_min + x_max) // 2
        cy = y_min + self.head_offset  # Headshot offset from top

        return (int(cx), int(cy))

    def _process_aim(self):
        """Aimbot — move mouse toward detected target."""
        t_start = time.perf_counter()

        screen = self.grabber.get_screen()
        target = self._detect_target(screen)

        if target is None:
            return

        cx, cy = target
        x_diff = cx - self.half_zone
        y_diff = cy - self.half_zone

        # Apply sensitivity and send movement
        move_x = x_diff * self.sensitivity
        move_y = y_diff * self.sensitivity

        self.arduinomouse.move(move_x, move_y)

        # Track latency
        elapsed = (time.perf_counter() - t_start) * 1000  # ms
        self._process_times.append(elapsed)
        if len(self._process_times) > 100:
            self._process_times.pop(0)
        self._avg_latency = sum(self._process_times) / len(self._process_times)

    def _process_trigger(self):
        """Triggerbot — click when crosshair is on target."""
        screen = self.grabber.get_screen()
        target = self._detect_target(screen)

        if target is None:
            return

        cx, cy = target

        # Check if target center is near crosshair (center of grab zone)
        if (abs(cx - self.half_zone) <= self.trig_threshold_x and
                abs(cy - self.half_zone) <= self.trig_threshold_y):
            self.arduinomouse.click()

    @property
    def latency(self):
        """Average processing latency in milliseconds."""
        return self._avg_latency

    @property
    def capture_fps(self):
        """Screen capture FPS."""
        return self.grabber.fps

    def close(self):
        """Shutdown all components."""
        self._running = False
        if hasattr(self, 'arduinomouse'):
            self.arduinomouse.close()
        if hasattr(self, 'grabber'):
            self.grabber.stop()
        self.toggled = False

    def __del__(self):
        self.close()
