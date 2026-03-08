"""
ui/futuristic_effects.py - Animated visual effects for the near-future UI.
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QTimer,
    Qt,
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


class DynamicBackgroundWidget(QWidget):
    """Animated cyber-grid background with particles and scan beam."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dynamicBackground")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._phase = 0.0
        self._particles = []

        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS for low CPU use
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._particles or len(self._particles) < 36:
            self._seed_particles(42)

    def _seed_particles(self, count: int):
        width = max(1, self.width())
        height = max(1, self.height())
        self._particles = []
        for _ in range(count):
            self._particles.append(
                {
                    "x": random.uniform(0.0, float(width)),
                    "y": random.uniform(0.0, float(height)),
                    "size": random.uniform(1.2, 3.2),
                    "speed": random.uniform(0.15, 0.65),
                    "drift": random.uniform(-0.45, 0.45),
                    "phase": random.uniform(0.0, math.tau),
                }
            )

    def _tick(self):
        self._phase += 0.025
        width = max(1, self.width())
        height = max(1, self.height())

        for particle in self._particles:
            particle["y"] += particle["speed"]
            particle["x"] += math.sin(self._phase + particle["phase"]) * particle["drift"]
            if particle["y"] > height + 6:
                particle["y"] = -6
                particle["x"] = random.uniform(0.0, float(width))
            if particle["x"] < -6:
                particle["x"] = width + 6
            elif particle["x"] > width + 6:
                particle["x"] = -6

        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        width = rect.width()
        height = rect.height()
        if width <= 0 or height <= 0:
            return

        base = QLinearGradient(0, 0, width, height)
        base.setColorAt(0.0, QColor(5, 9, 16))
        base.setColorAt(0.45, QColor(7, 14, 28))
        base.setColorAt(1.0, QColor(3, 6, 12))
        painter.fillRect(rect, base)

        # Floating radial glows.
        glow_points = (
            (
                width * (0.22 + 0.04 * math.sin(self._phase * 0.55)),
                height * (0.20 + 0.03 * math.cos(self._phase * 0.45)),
                max(width, height) * 0.42,
                QColor(0, 224, 255, 52),
            ),
            (
                width * (0.74 + 0.04 * math.cos(self._phase * 0.70)),
                height * (0.34 + 0.05 * math.sin(self._phase * 0.62)),
                max(width, height) * 0.38,
                QColor(132, 98, 255, 42),
            ),
            (
                width * (0.54 + 0.06 * math.sin(self._phase * 0.42)),
                height * (0.78 + 0.04 * math.cos(self._phase * 0.56)),
                max(width, height) * 0.35,
                QColor(24, 255, 176, 30),
            ),
        )
        for cx, cy, radius, color in glow_points:
            glow = QRadialGradient(cx, cy, radius)
            glow.setColorAt(0.0, color)
            glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillRect(rect, glow)

        # Perspective-style neon grid.
        horizon = int(height * 0.28)
        painter.setPen(QPen(QColor(36, 114, 168, 60), 1))
        for index in range(1, 17):
            y = horizon + int(((index / 16.0) ** 1.65) * (height - horizon + 30))
            painter.drawLine(0, y, width, y)

        center_x = width / 2.0
        scan_shift = math.sin(self._phase * 0.9) * 20.0
        for index in range(-12, 13):
            ratio = index / 12.0
            x_bottom = center_x + ratio * (width * 0.78) + scan_shift
            x_top = center_x + ratio * (width * 0.12)
            painter.drawLine(int(x_bottom), height + 2, int(x_top), horizon)

        # Horizontal scan beam.
        beam_y = int((self._phase * 105.0) % (height + 180)) - 90
        beam = QLinearGradient(0, beam_y, 0, beam_y + 120)
        beam.setColorAt(0.0, QColor(0, 220, 255, 0))
        beam.setColorAt(0.5, QColor(0, 220, 255, 36))
        beam.setColorAt(1.0, QColor(0, 220, 255, 0))
        painter.fillRect(0, beam_y, width, 120, beam)

        # Star-like particles.
        painter.setPen(Qt.NoPen)
        for particle in self._particles:
            pulse = 0.55 + 0.45 * math.sin(self._phase * 2.0 + particle["phase"])
            alpha = int(60 + 120 * pulse)
            color = QColor(94, 244, 255, alpha)
            painter.setBrush(color)
            size = particle["size"] * (0.7 + 0.7 * pulse)
            painter.drawEllipse(
                int(particle["x"]),
                int(particle["y"]),
                int(max(1.0, size)),
                int(max(1.0, size)),
            )


class ScanlineOverlay(QWidget):
    """Animated scanline overlay for cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._active = False
        self._phase = 0.0
        self._accent = QColor("#00E8FF")

        self._timer = QTimer(self)
        self._timer.setInterval(26)
        self._timer.timeout.connect(self._tick)

    def set_active(self, active: bool, accent: QColor | None = None):
        self._active = active
        if accent is not None:
            self._accent = accent
        if active:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        self._phase += 0.04
        self.update()

    def paintEvent(self, event):
        del event
        if not self._active:
            return

        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        sweep_y = int((self._phase * 140.0) % (height + 72)) - 36
        sweep = QLinearGradient(0, sweep_y, 0, sweep_y + 72)
        sweep.setColorAt(0.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 0))
        sweep.setColorAt(0.45, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 38))
        sweep.setColorAt(1.0, QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 0))
        painter.fillRect(0, sweep_y, width, 72, sweep)

        line_y = int((self._phase * 180.0) % height)
        painter.setPen(QPen(QColor(self._accent.red(), self._accent.green(), self._accent.blue(), 85), 1))
        painter.drawLine(0, line_y, width, line_y)


def fade_in_widget(widget: QWidget, delay_ms: int = 0, duration_ms: int = 460) -> QSequentialAnimationGroup:
    """Apply and return a fade-in animation for a widget."""
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)

    group = QSequentialAnimationGroup(widget)
    if delay_ms > 0:
        pause = QPropertyAnimation(widget, b"pos", widget)
        pause.setDuration(delay_ms)
        pause.setStartValue(QPoint(widget.pos()))
        pause.setEndValue(QPoint(widget.pos()))
        group.addAnimation(pause)
    group.addAnimation(animation)

    widget._fade_effect = effect
    widget._fade_animation = group
    return group
