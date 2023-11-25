import pygame
import sys
import os
from queue import Queue
from copy import deepcopy

W = 1200
H = 600
FPS = 60

VALID_IMAGE_FORMATS = ["png", "jpg"]

class ImageManager:
    
    @staticmethod
    def load(path, colorkey=None):
        """
        load an image params:
        path -> path to the image being loaded
        colorkey -> If it is not None, sets a colorkey to the image
        """
        img = pygame.image.load(path).convert()
        if colorkey:
            img.set_colorkey(colorkey)
        return img
    
    @staticmethod
    def load_image_scale(path,scale,colorkey=None):
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (scale, scale))
        if colorkey:
            img.set_colorkey(colorkey)
        return img

    @staticmethod
    def get_image(image,x,y,w,h,scale):
        surf = pygame.Surface((w,h))
        surf.set_colorkey((0,0,0))
        surf.blit(image, (0,0), (x,y,w,h))
        return pygame.transform.scale(surf, (w*scale, h*scale))

    @staticmethod
    def load_folder(folder_path):
        folder_list = os.listdir(folder_path)
        img_list = []
        for file in folder_path:
            if file.split('.')[1] in VALID_IMAGE_FORMATS:
                img_list.append(pygame.image.load(f"{folder_path}.{file}").convert())

        return img_list


class TileBtn:
    def __init__(self, image: pygame.Surface, tile_id, rect: pygame.Rect):
        self.image = image
        self.tile_id = tile_id
        self.rect = rect
    
    def draw(self, surf):
        surf.blit(self.image, self.rect)
    
    def click(self, pos):
        if pygame.mouse.get_pressed()[0]:
            if self.rect.collidepoint(pos):
                return True
         
        return False
            

class LevelEditor:
    def __init__(self):
        # Application setup
        self.screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        
        # Level Info
        # Also will be the default info
        self.name = "default"
        self.path = "^"
        self.tilesize = 20
        self.level_data = {}
        self.current_tile = 1
        self.tileset = {}
        self.tile_index = 1
        self.world_left = 0
        self.world_right = self.tilesize
        self.world_top = 0
        self.world_bottom = self.tilesize
        
        # Level editor stuff
        self.zoom = 1
        self.scroll = [0, 0]
        self.scroll_speed = 5
        self.mouse_scroll = [False, 0]
        self.buttons = []
        self.og_select_pos = [0, 0]
        self.selection_rect = pygame.Rect(0, 0, 0, 0)
        self.copied_data = []
        self.selection = False
        self.ctrl = False
        self.edit_mode = "Place"
        
        self.load_tileset("20_20.png", {"width":20, "height":20, "colorkey":(255, 255, 255)})
        
    def load_tileset(self, path, load_data):
        tileset = ImageManager.load(path, load_data["colorkey"])
        w = tileset.get_width()
        h = tileset.get_height()
        
        for i in range(int(h/load_data["height"])):
            for j in range(int(w/load_data["width"])):
                section = [j*load_data["width"], i*load_data["height"], load_data["width"],load_data["height"]]
                img = ImageManager.get_image(tileset, section[0], section[1], section[2], section[3], 1)
                self.tileset[self.tile_index] = img
                
                self.tile_index += 1
        
        row = 0
        col = 0
        for i, tile_id in enumerate(self.tileset):
            img = self.tileset[tile_id]
            btn = TileBtn(img, tile_id, pygame.Rect((col*load_data["width"])*1.4 + 20, (row*load_data["height"])*1.4 + 20 , load_data["width"], load_data["height"]))
            self.buttons.append(btn)
            
            col += 1
            
            if col >= 4:
                row += 1
                col = 0
    
    def get_tile_id(self, tile_pos):
        return f"{tile_pos[0]}/{tile_pos[1]}"
    
    def flood_fill(self, old_tile, new_tile, tile_pos):
        queue = Queue()
        
        def is_valid(pos):
            if pos[0] < self.world_left or pos[0] > self.world_right or pos[1] < self.world_top or pos[1] > self.world_bottom:
                return False
            if self.get_tile_id(pos) not in self.level_data:
                if old_tile[0] == 0:
                    return True
                else:
                    return False
            if self.get_tile_id(pos) in self.level_data:
                if self.level_data[self.get_tile_id(pos)][0] != old_tile[0] or self.level_data[self.get_tile_id(pos)][0] == new_tile[0]:
                    return False
                
            return True
        
        if self.get_tile_id(tile_pos) in self.level_data:
            if self.level_data[self.get_tile_id(tile_pos)][0] == new_tile[0]:
                return
            
        queue.put(tile_pos)
        
        while not queue.empty():
            pos = queue.get()
            adj = [
                [pos[0]-1, pos[1]],
                [pos[0]+1, pos[1]],
                [pos[0], pos[1]-1],
                [pos[0], pos[1]+1]
            ]
            
            if is_valid(adj[0]):
                self.level_data[self.get_tile_id(adj[0])] = [new_tile[0], adj[0], new_tile[2]]
                queue.put(adj[0])
            if is_valid(adj[1]):
                self.level_data[self.get_tile_id(adj[1])] = [new_tile[0], adj[1], new_tile[2]]
                queue.put(adj[1])
            if is_valid(adj[2]):
                self.level_data[self.get_tile_id(adj[2])] = [new_tile[0], adj[2], new_tile[2]]
                queue.put(adj[2])
            if is_valid(adj[3]):
                self.level_data[self.get_tile_id(adj[3])] = [new_tile[0], adj[3], new_tile[2]]
                queue.put(adj[3])
    
    def del_selected(self):
        if self.selection_rect.width > 0 or self.selection_rect.height > 0:
            pos = [int(self.selection_rect.x/self.tilesize), int(self.selection_rect.y/self.tilesize)]
            Range = [pos[0]+int(self.selection_rect.width/self.tilesize), pos[1]+int(self.selection_rect.height/self.tilesize)]
            
            for y in range(pos[1], Range[1]):
                for x in range(pos[0], Range[0]):
                    tile_pos = [x, y]
                    
                    if self.get_tile_id(tile_pos) in self.level_data:
                        del self.level_data[self.get_tile_id(tile_pos)]
        
        self.selection_rect = pygame.Rect(0, 0, 0, 0)
    
    def copy_selected(self):
        if self.selection_rect.width > 0 or self.selection_rect.height > 0:
            self.copied_data = []
            pos = [int(self.selection_rect.x/self.tilesize), int(self.selection_rect.y/self.tilesize)]
            Range = [pos[0]+int(self.selection_rect.width/self.tilesize), pos[1]+int(self.selection_rect.height/self.tilesize)]
            
            for y in range(pos[1], Range[1]):
                for x in range(pos[0], Range[0]):
                    tile_pos = [x, y]
                    
                    if self.get_tile_id(tile_pos) in self.level_data:
                        tile = deepcopy(self.level_data[self.get_tile_id(tile_pos)])
                        tile[1] = [-(pos[0]-(x)), -(pos[1]-(y))]
                        self.copied_data.append(tile)
        
        self.selection_rect = pygame.Rect(0, 0, 0, 0)
        
    def paste_selected(self, pos):
        for tile in self.copied_data:
            new_pos = [pos[0]+tile[1][0], pos[1]+tile[1][1]]
            
            self.level_data[self.get_tile_id(new_pos)] = [tile[0], new_pos, tile[2]]
    
    def run(self):
        
        while self.running:
            self.screen.fill((127, 127, 127))
            self.clock.tick(FPS)
            
            m_pos = pygame.mouse.get_pos()
            tile_pos = [int((m_pos[0]+self.scroll[0])/self.tilesize), int((m_pos[1]+self.scroll[1])/self.tilesize)]
            if tile_pos[0] < 0:
                tile_pos[0] -= 1
            if tile_pos[1] < 0:
                tile_pos[1] -= 1
            
            if pygame.key.get_pressed()[pygame.K_LEFT]:
                self.scroll[0] -= self.scroll_speed
            if pygame.key.get_pressed()[pygame.K_RIGHT]:
                self.scroll[0] += self.scroll_speed
            if pygame.key.get_pressed()[pygame.K_UP]:
                self.scroll[1] -= self.scroll_speed
            if pygame.key.get_pressed()[pygame.K_DOWN]:
                self.scroll[1] += self.scroll_speed
            
            if self.mouse_scroll[0]:
                dif = [(m_pos[0]-self.mouse_scroll[1][0]), (m_pos[1]-self.mouse_scroll[1][1])]
                self.scroll = dif
            
            if pygame.mouse.get_pressed()[0] and m_pos[0] > 200:
                
                if self.edit_mode == "Place":
                    if tile_pos[0] < self.world_left:
                        self.world_left = tile_pos[0]
                    if tile_pos[0] > self.world_right:
                        self.world_right = tile_pos[0]
                    if tile_pos[1] < self.world_top:
                        self.world_top = tile_pos[1]
                    if tile_pos[1] > self.world_bottom:
                        self.world_bottom = tile_pos[1]
                    
                    if self.get_tile_id(tile_pos) not in self.level_data:
                        self.level_data[self.get_tile_id(tile_pos)] = [self.current_tile, tile_pos, {}]
                    elif self.level_data[self.get_tile_id(tile_pos)][0] != self.current_tile:
                        self.level_data[self.get_tile_id(tile_pos)] = [self.current_tile, tile_pos, {}]
                
                if self.edit_mode == "Erase":
                    if self.get_tile_id(tile_pos) in self.level_data:
                        del self.level_data[self.get_tile_id(tile_pos)]
            
            for tile_id in self.level_data:
                tile = self.level_data[tile_id]
                if tile[0] in self.tileset:
                    self.screen.blit(self.tileset[tile[0]], (tile[1][0]*self.tilesize-self.scroll[0], tile[1][1]*self.tilesize-self.scroll[1]))
            
            if self.selection and (not self.ctrl):
                dif = [(tile_pos[0]-self.og_select_pos[0]+1)*self.tilesize, (tile_pos[1]-self.og_select_pos[1]+1)*self.tilesize]
                
                self.selection_rect.x = self.og_select_pos[0]*self.tilesize
                self.selection_rect.y = self.og_select_pos[1]*self.tilesize
                self.selection_rect.width = dif[0]
                self.selection_rect.height = dif[1]
                
                if dif[0] < 0:
                    self.selection_rect.x = self.selection_rect.x + dif[0]
                    self.selection_rect.width = -dif[0]
                
                if dif[1] < 0:
                    self.selection_rect.y = self.selection_rect.y + dif[1]
                    self.selection_rect.height = -dif[1]
                
            pygame.draw.rect(self.screen, (255, 0, 0), (self.selection_rect.x-self.scroll[0], 
                                                        self.selection_rect.y-self.scroll[1],
                                                        self.selection_rect.width,
                                                        self.selection_rect.height), 2)
            
            pygame.draw.rect(self.screen, (100, 80, 200), (0, 0, 200, 600)) 
                
            for btn in self.buttons:
                btn.draw(self.screen)
                if btn.click(m_pos):
                    self.current_tile = btn.tile_id
                
                if self.current_tile == btn.tile_id:
                    pygame.draw.rect(self.screen, (255, 0, 0), btn.rect, 2)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = True
                    
                    if event.key == pygame.K_c:
                        if self.ctrl:
                            self.copy_selected()
                    
                    if event.key == pygame.K_v:
                        if self.ctrl:
                            self.paste_selected(tile_pos)
                    
                    if event.key == pygame.K_b:
                        self.edit_mode = "Place"
                    
                    if event.key == pygame.K_e:
                        self.edit_mode = "Erase"
                    
                    if event.key == pygame.K_DELETE:
                        self.del_selected()
                    
                    if event.key == pygame.K_f:
                        if self.get_tile_id(tile_pos) in self.level_data:
                            self.flood_fill(self.level_data[self.get_tile_id(tile_pos)], [self.current_tile, 0, {}], tile_pos)
                        else:
                            self.flood_fill([0, 0, {}], [self.current_tile, 0, {}], tile_pos)
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = False
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 2:
                        self.mouse_scroll = [True, [m_pos[0]-self.scroll[0], m_pos[1]-self.scroll[1]]]
                    
                    if event.button == 3:
                        self.selection = True
                        self.og_select_pos = [int((m_pos[0]+self.scroll[0])/self.tilesize), int((m_pos[1]+self.scroll[1])/self.tilesize)]
                        self.selection_rect = pygame.Rect(0, 0, 0, 0)
                    
                    if event.button == 4:
                        self.current_tile = max(self.current_tile-1, 1)
                    if event.button == 5:
                        self.current_tile = min(self.current_tile+1, self.tile_index-1) 
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 2:
                        self.mouse_scroll = [False, 0]
                    if event.button == 3:
                        self.selection = False
            
            pygame.display.update()
            
            
LevelEditor().run()

pygame.quit()
sys.exit()

