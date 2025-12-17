# -*- coding: utf-8 -*-
"""
Feedback fractal with time-dependent warp specs
and layered modulation (LFO + drift).
"""

import math
import random
import cv2
import numpy as np


# ============================================================
# Time-dependent parameter generators
# ============================================================

class LFO:
    """Periodic modulation (fast or slow)."""

    def __init__(self, base, amplitude, frequency, phase=0.0):
        self.base = base
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def value(self, t):
        return self.base + self.amplitude * math.cos(
            self.frequency * t + self.phase
        )


class Drift:
    """Very slow, organic random walk."""

    def __init__(self, base, speed=0.0001, scale=1.0):
        self.base = base
        self.speed = speed
        self.scale = scale
        self.state = random.uniform(-1.0, 1.0)

    def value(self, t):
        self.state += random.uniform(-1.0, 1.0) * self.speed
        self.state *= 0.999  # damping
        return self.base + self.scale * self.state


class Modulated:
    """Layer multiple modulators together."""

    def __init__(self, *sources):
        self.sources = sources

    def value(self, t):
        return sum(src.value(t) for src in self.sources)


# ============================================================
# Warp specification
# ============================================================

class WarpSpec:
    """A warp whose parameters evolve over time."""

    def __init__(self, cx, cy, angle, scale, tx, ty):
        self.cx = cx
        self.cy = cy
        self.angle = angle
        self.scale = scale
        self.tx = tx
        self.ty = ty

    def evaluate(self, t):
        return dict(
            cx=self.cx.value(t),
            cy=self.cy.value(t),
            angle=self.angle.value(t),
            scale=self.scale.value(t),
            tx=self.tx.value(t),
            ty=self.ty.value(t),
        )


# ============================================================
# Main feedback fractal system
# ============================================================

class FeedbackFractal:
    def __init__(self, width=500, height=500, window_name="Feedback Fractal"):
        self.width = width
        self.height = height
        self.window_name = window_name

        self.img_current = np.zeros((height, width, 3), np.uint8)
        self.img_previous = np.zeros_like(self.img_current)

        self.counter = 0.0
        self.angle = 0.0

        self._initialize_noise()
        self._create_warps()

    # --------------------------------------------------------

    def _initialize_noise(self):
        self.img_current = np.random.randint(
            0, 256, (self.height, self.width, 3), dtype=np.uint8
        )

    # --------------------------------------------------------

    def _rotation_matrix(self, cx, cy, angle, scale):
        m = cv2.getRotationMatrix2D((cx, cy), angle, scale)
        m = np.vstack([m, [0, 0, 1]])
        return m

    # --------------------------------------------------------

    def _feedback_warp(self, img, cx, cy, angle, scale, tx, ty):
        m_rot = self._rotation_matrix(cx, cy, angle, scale)

        m_trans = np.array(
            [
                [1.0, 0.0, tx],
                [0.0, 1.0, ty],
                [0.0, 0.0, 1.0],
            ]
        )

        m = m_trans @ m_rot
        return cv2.warpPerspective(img, m, (self.width, self.height))

    # --------------------------------------------------------

    def _create_warps(self):
        """Define the feedback warp graph."""
        self.warps = [

            WarpSpec(
                cx=Modulated(
                    LFO(self.width / 2, 20, 0.001),
                    Drift(0, scale=5),
                ),
                cy=Modulated(
                    LFO(self.height / 2, 20, 0.0015),
                    Drift(0, scale=5),
                ),
                angle=LFO(0, 180, 0.002),
                scale=Modulated(
                    LFO(0.7, 0.2, 0.001),
                    Drift(0, scale=0.05),
                ),
                tx=LFO(0, self.width * 0.3, 0.0007),
                ty=LFO(0, self.height * 0.2, 0.0009),
            ),

            WarpSpec(
                cx=LFO(self.width / 2, 30, 0.0007),
                cy=LFO(self.height / 2, 30, 0.0009),
                angle=LFO(90, 90, 0.0013),
                scale=Modulated(
                    LFO(0.5, 0.2, 0.0008),
                    Drift(0, scale=0.08),
                ),
                tx=LFO(0, -self.width * 0.4, 0.001),
                ty=LFO(0, -self.height * 0.15, 0.0011),
            ),

            WarpSpec(
                cx=LFO(self.width / 2, 40, 0.0005),
                cy=LFO(self.height / 2, 40, 0.0006),
                angle=LFO(30, 60, 0.002),
                scale=LFO(0.3, 0.15, 0.001),
                tx=LFO(0, -self.width * 0.5, 0.0006),
                ty=LFO(0, -self.height * 0.4, 0.0007),
            ),
        ]

    # --------------------------------------------------------

    def update(self):
        self.counter += 10.0
        self.angle += 1.0

        warped_images = []

        for warp in self.warps:
            params = warp.evaluate(self.counter)
            warped = self._feedback_warp(self.img_current, **params)
            warped_images.append(warped)

        combined = warped_images[0]
        for img in warped_images[1:]:
            combined = cv2.addWeighted(combined, 1.0, img, 1.0, 0)

        # Zoom pulse
        zoom = 1.1 + 0.1 * math.cos(0.002 * self.counter)
        zoom_m = cv2.getRotationMatrix2D(
            (self.width / 2, self.height / 2), 0, zoom
        )
        combined = cv2.warpAffine(combined, zoom_m, (self.width, self.height))

        cv2.normalize(combined, combined, 0, 255, cv2.NORM_MINMAX)
        colored = cv2.addWeighted(
            combined,
            0.9,
            cv2.applyColorMap(combined, cv2.COLORMAP_HSV),
            0.1,
            0,
        )

        self.img_previous = self.img_current.copy()
        self.img_current = cv2.addWeighted(
            colored, 0.9, self.img_previous, 0.1, 0
        )

    # --------------------------------------------------------

    def run(self):
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        while True:
            self.update()
            cv2.imshow(self.window_name, self.img_current)

            if cv2.waitKey(30) & 0xFF == ord("q"):
                break

        cv2.destroyAllWindows()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    fractal = FeedbackFractal()
    fractal.run()

