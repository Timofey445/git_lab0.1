#!/usr/bin/env python3
# coding:utf-8
import os
import random
import socket
import sys
import time
import json
import zlib
from random import choice
import pygame

from const import Const

DATA_WIND = Const.data['DATA_WIND']
SIZE_MUL = 2
l_text, h_text, step_text = 200, 200, 70
background = pygame.Color((0, 50, 0))


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class MainMenu:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)
        self.sound = pygame.mixer.Sound('data/menu_click.ogg')
        self.image = pygame.transform.scale(load_image('fon.png'), size)
        self.image_cobra = pygame.transform.scale(load_image('cobra.png'), (600, 500))
        self.font = pygame.font.Font(size=50)
        self.font_title = pygame.font.Font('data/Capsmall.ttf', size=70)
        self.title = self.font_title.render('ЗМЕИНЫЕ ГОНКИ', True, 'yellow')
        self.text_game = [(self.font.render('Начать игру', True, 'darkred'),
                           self.font.render('Начать игру', True, 'orange')),
                          (self.font.render('Выход', True, 'darkred'),
                           self.font.render('Выход', True, 'orange'))]
        self.text_rect = []
        for i, surface in enumerate(self.text_game):
            rect = surface[0].get_rect()
            rect = rect.move(l_text, h_text + i * step_text)
            self.text_rect.append(rect)
        # print(self.text_rect)

    def exec(self, scr: pygame.Surface):
        mouse_pos = 0, 0
        click = False
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click = True
                if event.type == pygame.MOUSEMOTION:
                    mouse_pos = event.pos
            scr.fill('black')
            scr.blit(self.image, (0, 0))
            scr.blit(self.image_cobra, (width - 650, height - 600))
            lx = width // 2 - self.title.get_rect().width // 2
            scr.blit(self.title, (lx, 50))
            for i, (surface, rect) in enumerate(zip(self.text_game, self.text_rect)):
                if rect.collidepoint(mouse_pos):
                    k = 1
                    if click:
                        self.sound.play()
                        return i == 0
                else:
                    k = 0
                scr.blit(surface[k], rect)
            click = False
            text = self.font.render(f"Компьютер: {self.hostname} | IP адрес: {self.local_ip}",
                                    True, 'gray')
            scr.blit(text, (width // 2 - text.get_rect().width // 2, height - 50))
            pygame.display.flip()


pygame.init()
size = width, height = Const.WIDTH, Const.HEIGHT
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

# clock_tm = False
# fps = 4
color = choice(['white', 'red', 'blue', 'green', 'yellow'])
rnd = ['left', 'right', 'up', 'down']
buff = ''
my_addr = '-.-.-.-'
sound_brake = pygame.mixer.Sound('data/break1.ogg')
sound_eat = pygame.mixer.Sound('data/eat.ogg')
sound_ataka = pygame.mixer.Sound('data/brake.ogg')

font_win = pygame.font.Font('data/Capsmall.ttf', 50)
img_list = [load_image('snake.png')]
font = pygame.font.Font('data/Capsmall.ttf', size=20)

with open('config.json') as f:
    data = json.load(f)
    print(data)
    s_port = data.get('PORT')
    s_host = data.get('HOST')
    if s_port:
        Const.data['PORT'] = int(s_port)
    if s_host:
        Const.data['HOST'] = s_host


def prepare_head(body, radius, *args):
    snake_head = img_list[0]
    if len(body) == 1:
        return None, None
    _img = pygame.transform.scale(snake_head, (radius * 2, radius * 2))
    dx = body[0][0] - body[1][0]
    dy = body[0][1] - body[1][1]
    _shift_x, _shift_y = -(radius // 2), radius
    if dx < 0:
        _img = pygame.transform.flip(_img, True, False)
        _shift_x = radius * 2
    if dy < 0:
        _img = pygame.transform.rotate(_img, 90)
        _shift_y = radius
        _shift_x = radius * 2
    elif dy > 0:
        _img = pygame.transform.rotate(_img, -90)
        _shift_y = 0
        _shift_x = -(radius // 2)
    _rect = _img.get_rect().move(body[0][0] - radius, body[0][1] - radius)
    return _img, _rect, _shift_x, _shift_y


def play_sound(sound: str, addr=''):
    if addr != my_addr:
        return
    if 'break' in sound:
        sound_brake.play()
    elif 'eat' in sound:
        sound_eat.play()
    elif 'ataka' in sound:
        sound_ataka.play()


# def time_func():
#     global clock_tm
#     clock_tm = False


play_sound('eat')
game = True
menu = MainMenu()
convert_error = True
tm_winner = ''
while game:
    game = menu.exec(screen)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Подключение к серверу: {Const.data['HOST']}:{Const.data['PORT']}")
            s.connect((Const.data['HOST'], Const.data['PORT']))
            my_addr = s.getsockname()[0]
            print(' ADDR:', my_addr)
            flag = game
            end_clr = [255, 255, 255]
            while flag:
                cmd = {'key': []}
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        flag = False
                    if event.type == (pygame.USEREVENT + 1000):
                        tm_winner = ''
                        print('event')
                        break
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        flag = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        cmd['pos'] = event.pos
                keys = pygame.key.get_pressed()
                if any(keys):
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        cmd['key'].append("left")
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        cmd['key'].append("right")
                    if keys[pygame.K_UP] or keys[pygame.K_w]:
                        cmd['key'].append("up")
                    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                        cmd['key'].append("down")
                st = json.dumps(cmd)
                try:
                    s.send(st.encode())
                except Exception as err:
                    print('Error of send:', err)
                try:
                    buff += zlib.decompress(s.recv(DATA_WIND)).decode()
                    # print(buff)
                except Exception as err:
                    print('Error of receive:', err)

                data = dict()
                while buff.find('%%%%%') >= 0:
                    pos = buff.find('%%%%%')
                    data = buff[5:pos]
                    buff = buff[pos + 5:]
                    convert_error = True
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        print('JSON convert error.', data)
                        convert_error = False
                        continue
                    except Exception as err:
                        print('==> ', err)
                        continue

                if convert_error:
                    winner = data.get('WINNER', '')
                    if winner:
                        print('Победитель:', winner)
                        tm_winner = f"Победитель: {winner}"
                        pygame.time.set_timer(pygame.USEREVENT + 1000, 4000, 1)
                    tm = data.get('TIMER', 999)
                    pygame.display.set_caption(f"До конца раунда осталось: {tm} секунд...")
                    if tm < 2 or tm == 999:
                        screen.fill(pygame.Color(end_clr))
                        end_clr = end_clr[0] - 6, end_clr[1] - 4, end_clr[2] - 6
                    else:
                        end_clr = [250, 255, 250]
                        screen.fill(background)
                    #
                    for addr, player in data.get('players', dict()).items():
                        # print(player)
                        sound = player.get('sound', '')
                        if sound:
                            play_sound(sound, addr)
                        body = player['body']
                        figure = player['figure']
                        len_body = len(body)
                        hero_length = player['length']
                        hero_life = player['life']
                        radius = player['radius']
                        my_head = addr == my_addr
                        # print(radius)
                        color_r, color_g, color_b = player['color']
                        dr_color = (255 - color_r) // len_body
                        dg_color = (255 - color_g) // len_body
                        db_color = (255 - color_b) // len_body
                        txt_pos = [0, 0]
                        contour = 0
                        for i, pos in enumerate(body):
                            # surf_1 = font.render(f"{hero_length}", False,
                            #                      'lightblue', background)
                            surf_0 = font.render(f"{hero_life}", False,
                                                 'pink', background)
                            # screen.blit(surf_0, (txt_pos[0], txt_pos[1]))
                            # screen.blit(surf_1, (txt_pos[0] + 10, txt_pos[1]))
                            img, rect, *shift = prepare_head(body, player['radius'])

                            _radius = radius
                            if i == 0:
                                txt_pos = pos
                                div = min(2, len(body))
                                color = (color_r // div, color_g // div, color_b // div)
                                radius -= 4
                                if my_head and len(body) == 1:
                                    pygame.draw.circle(screen, 'red', pos, _radius + 4)
                                    pygame.draw.circle(screen, 'white', pos, _radius)
                                else:
                                    if not img:
                                        pygame.draw.circle(screen, color, pos, _radius, contour)
                            else:
                                color = (color_r + dr_color * i,
                                         color_g + dg_color * i,
                                         color_b + db_color * i)
                                radius = max(3, radius / 1.1)
                                pygame.draw.circle(screen, color, pos, _radius, contour)
                                contour = 2
                        # pygame.draw.circle(screen, color, pos, _radius + 2)
                        if img:
                            screen.blit(img, rect)
                            screen.blit(surf_0, (rect[0] + shift[0], rect[1] + shift[1]))
                        if tm_winner:
                            surf = font_win.render(tm_winner, False, 'white')
                            screen.blit(surf, (50, 50))
                    pygame.display.flip()
                    # clock.tick(fps)
    except ConnectionResetError:
        print('Try reconnect')
        continue
    # except Exception as err:
    #     print('All errors: ', err)
pygame.quit()
sys.exit()
