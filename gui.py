# Pygame Gui system
import pygame
import sys
import os
import subprocess
import random

def init():
    pygame.init()
    pygame.font.init()

class Window:
    def __init__(self, pos, width, height, title):
        self.rect = pygame.FRect(pos[0], pos[1], width, height)
        self.title = title
        self.surf = pygame.Surface((self.rect.width, self.rect.height))
        self.font = pygame.font.SysFont("Arial", 20)
        self.close_rect = pygame.FRect(0, 0, 25, 25)
        self.close_rect.right = width
        self.title_bar_rect = pygame.FRect(self.rect.x, self.rect.y, width, 26)
        self.rendered_title = self.font.render(self.title, False, (0, 0, 0))
        self.selected = False
        self.enabled = True
        self.clicked_pos = [0, 0]
        
        self.items = []
    
    def add_item(self, item):
        item.rect.y += 26
        self.items.append(item)
    
    def add_items(self, items):
        for item in items:
            item.rect.y += 26
            self.items.append(item)
    
    def draw(self, surf):
        self.surf.fill((110, 110, 110))
        
        for item in self.items:
            item.draw(self.surf)
        
        pygame.draw.rect(self.surf, (255, 0, 0), self.close_rect)
        pygame.draw.line(self.surf, (0, 0, 0), (0, 26), (self.rect.width, 26), 4)
        
        surf.blit(self.surf, self.rect)
    
    def update(self, args={}):
        for item in self.items:
            
            m_pos = pygame.mouse.get_pos()
            x = m_pos[0]-self.rect.x
            y = m_pos[1]-self.rect.y
            
            x = max(0, x)
            y = max(0, y)
            x = min(self.rect.width, x)
            y = min(self.rect.height, y)
            
            item.update({"mouse pos": [x, y]})
    
    def handle_event(self, event):
        for item in self.items:
            item.handle_event(event)
        
        
    
class Label:
    def __init__(self, pos, text):
        self.pos = pos
        self.text = text
        self.font = pygame.font.SysFont("Arial", 20)
        self.rendered_text = self.font.render(self.text, False, (0, 0, 0))
        self.rect = self.rendered_text.get_rect(topleft=self.pos)
        
    def draw(self, surf):
        surf.blit(self.rendered_text, self.pos)
    
    def update(self, args={}):
        pass
    
    def handle_event(self, event):
        pass
        

class Button:
    def __init__(self, pos, width, height, text, callback=None):
        self.id = random.randint(1, 1000000)
        self.rect = pygame.FRect(pos[0], pos[1], width, height)
        self.callback = callback
        self.font = pygame.font.SysFont("Arial", 20)
        self.text = text
        self.rendered_text = self.font.render(self.text, False, (255, 255, 255))
        self.clicked = False
        self.can_click = False
    
    def draw(self, surf):
        pygame.draw.rect(surf, (80, 80, 80), self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 4)
        surf.blit(self.rendered_text, (self.rect.centerx-self.rendered_text.get_width()/2, self.rect.centery-self.rendered_text.get_height()/2))
    
    def update(self, args={}):
        if "mouse pos" in args:
            self.can_click = False
            if self.rect.collidepoint(args["mouse pos"]):
                self.can_click = True
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.can_click:
                self.clicked = True
                if self.callback:
                    self.callback()
            
        if event.type == pygame.MOUSEBUTTONUP:
             if event.button == 1:
                self.clicked = False

class TextInput:
    def __init__(self, pos, width, height):
        self.id = random.randint(1, 1000000)
        self.pos = pos
        self.surf = pygame.Surface((width, height))
        self.rect = self.surf.get_rect(topleft=self.pos)
        self.text = ""
        self.font = pygame.font.SysFont("Arial", 20)
        self.active = False
    
    def draw(self, surf):    
        self.surf.fill((255, 255, 255))
        text = self.font.render(self.text, False, (0, 0, 0))
        pos = [10, self.surf.get_height()/2-text.get_height()/2]
        
        if text.get_width() > self.surf.get_width()-20:
            pos[0] -= (text.get_width()- self.surf.get_width())+20
        
        self.surf.blit(text, pos)
        
        surf.blit(self.surf, self.pos)
    
    def update(self, args={}):
        pass
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
            
