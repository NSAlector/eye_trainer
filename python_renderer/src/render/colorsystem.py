import math
import numpy
import cv2
from colormath.color_objects import LabColor, sRGBColor
from OpenGL.GL import *
from enumData.bltype import blType

class ColorSystem:
    def __init__(self):
        self.base_palettes = {
            blType.Healthy: {
                'primary':   LabColor(55, 45,  40),
                'secondary': LabColor(50, -50,  55),
                'accent':    LabColor(60,  15, -65),
                'extra':     LabColor(70,  60, -20),
            },
            blType.Deuteranopia: {
                # No green-red distinction
                'primary':   LabColor(65,  10,  60),   # strong yellow
                'secondary': LabColor(45, -10, -60),   # strong blue
                'accent':    LabColor(80,   0,  40),   # light yellow
                'extra':     LabColor(30,  20, -50),   # dark blue
            },
            blType.Protanopia: {
                # No red
                'primary':   LabColor(70, -40,  50),   # yellow-green
                'secondary': LabColor(50, -50, -30),   # cyan
                'accent':    LabColor(85,  -5,  65),   # bright yellow
                'extra':     LabColor(35, -30, -40),   # dark cyan
            },
            blType.Tritanopia: {
                # No blue-yellow
                'primary':   LabColor(50,  65,  30),   # vivid red
                'secondary': LabColor(55, -60,  20),   # vivid green
                'accent':    LabColor(75,  40,  15),   # light red
                'extra':     LabColor(35, -45,  10),   # dark green
            },
            blType.Achromatopsia: {
                # No color at all
                'primary':   LabColor(15, 0, 0),
                'secondary': LabColor(50, 0, 0),
                'accent':    LabColor(80, 0, 0),
                'extra':     LabColor(95, 0, 0),
            }
        }

    def get_base_color(self, blindness_type: blType, color_type='primary'):
        return self.base_palettes.get(
            blindness_type, self.base_palettes[blType.Healthy]
        )[color_type]

    def lab_to_rgb(self, color_lab: LabColor):
        try:
            rgb = color_lab.convert_to('sRGB')
            return (
                max(0.0, min(1.0, rgb.rgb_r)),
                max(0.0, min(1.0, rgb.rgb_g)),
                max(0.0, min(1.0, rgb.rgb_b)),
            )
        except:
            lab_array = numpy.array(
                [[[color_lab.lab_l, color_lab.lab_a, color_lab.lab_b]]],
                dtype=numpy.float32
            )
            bgr = cv2.cvtColor(lab_array, cv2.COLOR_LAB2BGR)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)[0][0]
            return (rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

    def generate_colors(self, bl: blType, x_norm, z_norm, time_val):
        palette = self.base_palettes[bl]
        colors = list(palette.values()) 

        variations = []
        for i, base in enumerate(colors):
            phase = i * math.pi / 2
            t = time_val * 0.4 + phase

            if bl == blType.Achromatopsia:
                # only vary lightness
                l_shift = 35 * math.sin(x_norm * math.pi * 2 + t)
                c = LabColor(
                    max(5, min(95, base.lab_l + l_shift)),
                    0, 0
                )
            else:
                a1 = x_norm * math.pi * 3 + t
                a2 = z_norm * math.pi * 3 + time_val * 0.5

                l_swing = 25 * math.sin(a1)
                a_swing = 50 * math.cos(a1 + a2)
                b_swing = 50 * math.sin(a2 + phase)

                c = LabColor(
                    max(10, min(90,  base.lab_l + l_swing)),
                    max(-100, min(100, base.lab_a + a_swing)),
                    max(-100, min(100, base.lab_b + b_swing)),
                )
            variations.append(c)

        return variations

    def calc_cur_color(self, bl: blType, ball_position, ground_size, current_time):
        x_norm = (ball_position[0] + ground_size) / (2 * ground_size)
        z_norm = (ball_position[2] + ground_size) / (2 * ground_size)

        colors = self.generate_colors(bl, x_norm, z_norm, current_time)

        idx = int((x_norm * 2 + math.sin(current_time * 0.7) + 1) * 1.5) % len(colors)
        return self.lab_to_rgb(colors[idx])

    def init_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.3, 0.3, 0.3, 1.0])
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    @staticmethod
    def set_background_color(bl_type: blType):
        if bl_type == blType.Achromatopsia:
            glClearColor(0.85, 0.85, 0.85, 1.0)
        elif bl_type == blType.Deuteranopia:
            glClearColor(0.1, 0.1, 0.25, 1.0)   # dark blue bg
        elif bl_type == blType.Protanopia:
            glClearColor(0.05, 0.15, 0.2, 1.0)  # dark cyan bg
        elif bl_type == blType.Tritanopia:
            glClearColor(0.1, 0.15, 0.05, 1.0)  # dark green bg
        else:
            glClearColor(0.15, 0.15, 0.25, 1.0)