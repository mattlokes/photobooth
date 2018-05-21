import pygame
import random
import operator
import os

from datetime import datetime
from glob import glob
from sys import exit

class ExtraTransforms:
    @staticmethod
    def aa_rotozoom(img, angle, scale, aa_border=5):
        for i in range(0, aa_border) + range(img.get_rect().size[1]-aa_border,img.get_rect().size[1]) :
            for j in range(0, img.get_rect().size[0]):
                img.set_at((j,i), (255,255,255,0))
        for i in range(0, aa_border) + range(img.get_rect().size[0]-aa_border,img.get_rect().size[0]) :
            for j in range(0, img.get_rect().size[1]):
                img.set_at((i,j), (255,255,255,0))
        img = pygame.transform.rotozoom(img, angle, scale)
        return img

    @staticmethod
    def set_alpha(img, alpha):
        alpha_img = pygame.Surface(img.get_rect().size, pygame.SRCALPHA)
        alpha_img.fill((255, 255, 255, alpha))
        img.blit(alpha_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return img

