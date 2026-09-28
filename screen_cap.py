"""
ScreenCapture — Ultra low-latency screen grabber.

Uses Windows DXGI Desktop Duplication (via d3dshot) for the fastest 
possible screen capture. Falls back to mss if d3dshot is unavailable.

Optimizations:
- DXGI Desktop Duplication: ~0.3-0.8ms per frame (vs mss ~3-5ms)
- Lock-free double buffering with numpy
- Direct numpy array output (no PIL conversion)
- Continuous capture thread with minimal overhead
"""

import numpy as np
import threading
import ctypes
import time

# Try to import the fastest capture method available
_USE_DXGI = False
try:
    import d3dshot
    _USE_DXGI = True
except ImportError:
    pass

if not _USE_DXGI:
    from mss import mss


class ScreenCapture:
    def __init__(self, x, y, grabzone):
        self.x = x
        self.y = y
        self.grabzone = grabzone
        
        # Double buffer — write to one, read from other (lock-free)
        self._buffers = [
            np.zeros((grabzone, grabzone, 4), dtype=np.uint8),
            np.zeros((grabzone, grabzone, 4), dtype=np.uint8)
        ]
        self._write_idx = 0  # Index of buffer being written to
        self._ready = False
        
        # Performance tracking
        self._frame_count = 0
        self._fps = 0.0
        self._last_capture_time = 0.0
        
        # DXGI capture
        self._d3d = None
        if _USE_DXGI:
            try:
                self._d3d = d3dshot.create(capture_output="numpy")
            except Exception:
                pass
        
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        """Continuous capture loop — runs in background thread."""
        if self._d3d is not None:
            self._capture_loop_dxgi()
        else:
            self._capture_loop_mss()

    def _capture_loop_dxgi(self):
        """DXGI Desktop Duplication capture — fastest method (~0.3-0.8ms)."""
        region = (self.x, self.y, self.x + self.grabzone, self.y + self.grabzone)
        start_time = time.perf_counter()
        frame_count = 0
        
        while self._running:
            try:
                frame = self._d3d.screenshot(region=region)
                if frame is not None:
                    write_idx = self._write_idx
                    # Ensure we have BGRA (4 channels) for consistency
                    if frame.shape[2] == 3:
                        self._buffers[write_idx][:, :, :3] = frame
                    else:
                        np.copyto(self._buffers[write_idx], frame[:self.grabzone, :self.grabzone])
                    # Swap buffers (atomic integer write = lock-free)
                    self._write_idx = 1 - write_idx
                    self._ready = True
                    self._last_capture_time = time.perf_counter()
                    
                    frame_count += 1
                    elapsed = time.perf_counter() - start_time
                    if elapsed >= 1.0:
                        self._fps = frame_count / elapsed
                        frame_count = 0
                        start_time = time.perf_counter()
            except Exception:
                pass

    def _capture_loop_mss(self):
        """MSS fallback capture (~3-5ms per frame)."""
        monitor = {
            "top": self.y,
            "left": self.x,
            "width": self.grabzone,
            "height": self.grabzone
        }
        start_time = time.perf_counter()
        frame_count = 0
        
        with mss() as sct:
            while self._running:
                try:
                    shot = sct.grab(monitor)
                    frame = np.array(shot, dtype=np.uint8)
                    
                    write_idx = self._write_idx
                    h, w = min(frame.shape[0], self.grabzone), min(frame.shape[1], self.grabzone)
                    self._buffers[write_idx][:h, :w] = frame[:h, :w]
                    self._write_idx = 1 - write_idx
                    self._ready = True
                    self._last_capture_time = time.perf_counter()
                    
                    frame_count += 1
                    elapsed = time.perf_counter() - start_time
                    if elapsed >= 1.0:
                        self._fps = frame_count / elapsed
                        frame_count = 0
                        start_time = time.perf_counter()
                except Exception:
                    pass

    def get_screen(self):
        """Get the latest captured frame as numpy array (BGRA/BGR)."""
        # Read from the buffer that's NOT being written to
        read_idx = 1 - self._write_idx
        return self._buffers[read_idx]

    @property
    def fps(self):
        """Current capture FPS."""
        return self._fps

    def stop(self):
        """Stop the capture loop."""
        self._running = False
