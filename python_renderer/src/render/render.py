import pygame
import time
import sys
import os
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from PIL import Image

import json
from src.render.scenes import scenes
from src.render.scenes import assert_dir

from enumData.bltype import blType

from src.render.colorsystem import ColorSystem
from datamanager.datamanager import DataManager

from utils.sharedMemoryFileWriter import SharedMemoryWriter

class SceneSetterTest:
    def __init__(self):
        self.textures = {}
    def load_texture(self, filename:str, tint:list):
        if filename in self.textures:
            return self.textures[filename]
        
        path = os.path.join(assert_dir(filename))
        img = Image.open(path).convert("RGBA")
        img_array = np.array(img, dtype=np.float32)

        img_array[:, :, 0] *= tint[0]
        img_array[:, :, 1] *= tint[1]
        img_array[:, :, 2] *= tint[2]
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     img.width, img.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, img_array)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        self.textures[filename] = tex_id
        return tex_id
    def load_scene(self, scene_json_path, bl_type):
        return {
            "bg_tex": self.load_texture("test_bg.png", [1.0, 1.0, 1.0]),
            "object_tex": self.load_texture("test_object.png", [1.0, 1.0, 1.0]),
        }

class SceneSetter:
    def __init__(self):
        self.textures = {}
    def load_texture(self, filename:str, tint:list):
        if filename in self.textures:
            return self.textures[filename]
        
        path = os.path.join(assert_dir(filename))
        img = Image.open(path).convert("RGBA")
        img_array = np.array(img, dtype=np.float32)

        img_array[:, :, 0] *= tint[0]
        img_array[:, :, 1] *= tint[1]
        img_array[:, :, 2] *= tint[2]
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     img.width, img.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, img_array)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        self.textures[filename] = tex_id
        return tex_id
    def load_scene(self, scene_json_path, bl_type):
        with open(scene_json_path) as f:
            data = json.load(f)
        
        scene_name = list(data.keys())[0]
        scene = data[scene_name]
        bl_key = bl_type.name

        return {
            "bg_tex":self.load_texture(
                        scene["bg"]["texture"],
                        scene["bg"]["tint"][bl_key]),
            "object_tex":self.load_texture(
                        scene["object"]["texture"],
                        scene["object"]["tint"][bl_key]),
        }


def create_fbo(w, h):
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glFramebufferTexture2D( GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D, tex, 0)

    assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    return fbo, tex

class BaseRenderer:
    def __init__(self, bl_type, movement_func, scene_type, speed, width=1920, height=1080):
        self.display_size = (width, height)
        self.bl_type = bl_type
        self.movement_func = movement_func
        self.session_manager = DataManager()
        self.cs = ColorSystem()
        self.ground_size = 12.0
        self.orbit_radius = 5.0
        self.ball_radius = 1.0
        self.speed = speed 
        self.edge_margin = 0.85
        if bl_type == blType.test:
            self.scene_setter = SceneSetterTest()
        else:
            self.scene_setter = SceneSetter()
        self.scene_data = None
        self.scene_type = scene_type
        self.fbo = None
        self.fbo_tex = None
        self.shm = None
    def _init_opengl(self):
        w, h = self.display_size
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glClearColor(0, 0, 0, 1)

    def draw_scene(self, position):
        w, h = self.display_size
        #self.scene_data = self.scene_setter.load_scene(self.scene_type, self.bl_type)
        px = (position[0] / (self.ground_size * self.edge_margin) + 1.0) * 0.5 * w
        py = (position[2] / (self.ground_size * self.edge_margin) + 1.0) * 0.5 * h

        obj_size = w * 0.06   # объект занимает ~6% ширины экрана

        glClear(GL_COLOR_BUFFER_BIT)

        glEnable(GL_TEXTURE_2D)
        glColor3f(1, 1, 1)
        glBindTexture(GL_TEXTURE_2D, self.scene_data["bg_tex"])
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(w, 0)
        glTexCoord2f(1, 1); glVertex2f(w, h)
        glTexCoord2f(0, 1); glVertex2f(0, h)
        glEnd()

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, self.scene_data["object_tex"])
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(px - obj_size, py - obj_size)
        glTexCoord2f(1, 0); glVertex2f(px + obj_size, py - obj_size)
        glTexCoord2f(1, 1); glVertex2f(px + obj_size, py + obj_size)
        glTexCoord2f(0, 1); glVertex2f(px - obj_size, py + obj_size)
        glEnd()
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
    def setup_camera(self):
        glLoadIdentity()
        glRotatef(90, 1, 0, 0)
        glTranslatef(0.0, -20.0, 0.0)

class EyeGymnasticsOne(BaseRenderer):
     def run(self):
        session_data = self.session_manager.start_session(
            self.bl_type, 
            self.movement_func.__name__
        )
        try:
            self.shm = SharedMemoryWriter("frames", self.display_size[0], self.display_size[1])
            
            pygame.init()
            pygame.display.set_mode(self.display_size, DOUBLEBUF | OPENGL | HIDDEN)
            #pygame.display.set_mode(self.display_size)

            pygame.display.set_caption(f"Eye Gymnastics - {self.bl_type.name}")
            
            self._init_opengl()
            
            self.scene_data = self.scene_setter.load_scene(self.scene_type, self.bl_type)
            
            self.fbo, self.fbo_tex = create_fbo(*self.display_size)

            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
            ball_position = [0, 0, 0]
            start_time = time.time()
            clock = pygame.time.Clock()
            running = True
            frame_count = 0
            max_duration = 40 
            while running:
                elapsed = time.time() - start_time
                
                if elapsed > max_duration:
                    print(f"[EyeGymnasticsOne] Max duration ({max_duration}s) reached, exiting")
                    break
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                
                current_time = time.time() - start_time
                ball_position[0], ball_position[1], ball_position[2] = self.movement_func(
                    current_time,
                    self.orbit_radius * self.edge_margin,
                    self.ground_size * self.edge_margin,
                    self.speed
                )

                glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
                self.draw_scene(ball_position)
                self.session_manager.log_coordinates(ball_position)

                w, h = self.display_size
                raw = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)
                img = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))                
                raw = np.flipud(img).tobytes()
                self.shm.write_frame(raw)
                
                frame_count += 1
                time.sleep(0.001)
                clock.tick(60)
            
            session_data["status"] = "completed"

        except KeyboardInterrupt:
            session_data["status"] = "interrupted"
        except Exception as e:
            import traceback
            traceback.print_exc()
            session_data["status"] = "error"
            self.session_manager.add_error(e)
        finally:
            self.session_manager.end_session(session_data)
            pygame.quit()

# class EyeGymnasticsTwo(BaseRenderer):
#     def run(self):
#         session_data = self.session_manager.start_session(
#             self.bl_type, self.movement_func.__name__
#         )
#         try:
#             self.shm = SharedMemoryWriter("frames", self.display_size[0], self.display_size[1])           
#             pygame.init()
#             pygame.display.set_mode(self.display_size, DOUBLEBUF | OPENGL | HIDDEN)
#             pygame.display.set_caption(f"Eye Gymnastics - {self.bl_type.name}")
#             self._init_opengl()

#             self.fbo, self.fbo_tex = create_fbo(*self.display_size)
#             glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

#             ball_positions = [[0, 0, 0], [0, 0, 0]]
#             start_time = time.time()
#             clock = pygame.time.Clock()
#             running = True

#             while running:
#                 for event in pygame.event.get():
#                     if event.type == pygame.QUIT: running = False
#                     elif event.type == pygame.KEYDOWN:
#                         if event.key == pygame.K_ESCAPE: running = False

#                 current_time = time.time() - start_time
#                 pos1 = self.movement_func(current_time, self.orbit_radius, self.ground_size* self.edge_margin, self.speed)
#                 ball_positions[0] = list(pos1)
#                 ball_positions[1] = [-pos1[0], pos1[1], pos1[2]]

#                 ball_colors = [
#                     self.cs.calc_cur_color(self.bl_type, ball_positions[0], 20.0, current_time),
#                     self.cs.calc_cur_color(self.bl_type, ball_positions[1], 20.0, current_time)
#                 ]
#                 self.session_manager.log_coordinates(ball_positions[0])

#                 self.cs.set_background_color(self.bl_type)
#                 glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
#                 glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#                 self._setup_camera()
#                 self._draw_ground(20.0)
#                 for pos, color in zip(ball_positions, ball_colors):
#                     self._draw_ball(pos, self.ball_radius, color)

#                 w, h = self.display_size
#                 raw = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)
#                 img = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))
#                 raw = np.flipud(img).tobytes()

#                 self.shm.write_frame(raw)
#                 time.sleep(0.001)
#                 clock.tick(60)

#             session_data["status"] = "completed"

#         except KeyboardInterrupt:
#             session_data["status"] = "interrupted"
#         except Exception as e:
#             import traceback
#             print(f"Error: {e}")
#             traceback.print_exc()
#             session_data["status"] = "error"
#             self.session_manager.add_error(e)
#         finally:
#             if self.shm: self.shm.close()
#             self.session_manager.end_session(session_data)
#             pygame.quit()