#!/usr/bin/env python3
# coding:utf-8
import datetime
import colorsys
import random
import socket
import sys
import time
import json
import zlib
import sqlite3
from random import randint

import pygame

from const import Const

pygame.init()
S_SIZE = S_WIDTH, S_HEIGHT = 850, 600
screen = pygame.display.set_mode(S_SIZE)
s_clock = pygame.time.Clock()
S_FPS = 14
ALIAS = False
# font = pygame.font.Font('data/Pressdarling.ttf', size=20)
font = pygame.font.Font('data/Capsmall.ttf', size=20)
font2 = pygame.font.Font('data/Capsmall.ttf', size=30)
ten_sound = pygame.mixer.Sound('data/ten_second.ogg')

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
packet_size = 0
DATA_WIND = Const.data['DATA_WIND']  # размер пакета данных
# FPS = 0.03  # частота цикла
# STEP_WAIT = 6
WIDTH, HEIGHT = Const.WIDTH, Const.HEIGHT
STEP = 10
RADIUS = 8
COUNT = 2
EAT_COUNT = 40
EAT_LIFE = 200
SIZE_MUL = 2
MIN_SAFE_LENGTH = 15

coords = set()
rnd = ['left', 'right', 'up', 'down']

con = sqlite3.connect('data/results.db')
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, addr VARCHAR(40), wins INTEGER);
                """)
if Const.restart:
    cur.execute("""DELETE FROM users""")
    con.commit()

win_stat = dict()


def get_sql_stat():
    global win_stat
    sql_stat = cur.execute("SELECT * FROM users").fetchall()
    win_stat = dict()
    for rec in sql_stat:
        win_stat[rec[1]] = rec[2]


# def random_coord():
#     x, y = 50, 50
#     while (x, y) in coords:
#         x = 50 * ((STEP * ((randint(50, WIDTH - 50)) // STEP)) // 50)
#         y = 50 * ((STEP * ((randint(50, HEIGHT - 50)) // STEP)) // 50)
#     coords.add((x, y))
#     return [x, y]
def random_coord():
    x = 50 * ((STEP * ((randint(50, WIDTH - 50)) // STEP)) // 50)
    y = 50 * ((STEP * ((randint(50, HEIGHT - 50)) // STEP)) // 50)
    return [x, y]



all_sprites = pygame.sprite.Group()
eat_sprites = pygame.sprite.Group()


class MySprite(pygame.sprite.Sprite):
    def __init__(self, pos, radius, color, *args):
        super().__init__(*args)
        self._radius = radius
        self.image, self.rect = self.new_radius(radius, color)
        self.move_point(pos)

    def move_point(self, pos):
        self.rect.x = pos[0] - self._radius
        self.rect.y = pos[1] - self._radius

    def new_radius(self, radius, color):
        image = pygame.Surface((radius * 2, radius * 2))
        pygame.draw.circle(image, color, (radius, radius), radius)
        self._radius = radius
        return image, image.get_rect()


class Color:
    data = [0.1, 0.95, 0.2, 0,85, 0.3, 0.75, 0.4, 0.65, 0.5,
            0.55, 0.6, 0.45, 0.7, 0.35, 0.8, 0.25, 0.9, 0.15]
    random.shuffle(data)
    count = 0

    def __init__(self):
        h, s, l = Color.data[Color.count], 0.9, 0.4 + random.random() / 5.0
        r, g, b = [int(256 * i) for i in colorsys.hls_to_rgb(h, l, s)]
        self.color = (r, g, b)
        Color.count = (Color.count + 1) % len(Color.data)


class Eat(MySprite):
    def __init__(self):
        self._pos = [0, 0]
        self._body = [random_coord()]
        self._radius = 8
        self._figure = 0
        self._color = (50, 255, 50)
        self._life = ''
        super().__init__(self._body[0], self._radius, self._color, eat_sprites)
        self._count = EAT_LIFE

    def get_data(self):
        return {'body': self._body, 'radius': self._radius, 'color': self._color,
                'figure': self._figure, 'length': '', 'life': self._life}

    def get_head(self):
        return self._body[0]

    def update(self):
        self._count -= 1
        r, g, b = self._color
        r = min(200, r + 1)
        g = max(10, g - 1)
        b = max(0, b - 1)
        self._color = (r, g, b)
        if self._count < 0:
            eat_sprites.remove(self)
        return self._count < 0


class Player(MySprite):
    def __init__(self, pos=None, radius=RADIUS):
        if pos is None:
            pos = random_coord()
        self._pos = [0, 0]
        self._body = [pos]
        self._inc = 0
        self._radius = radius
        self._data = dict()
        self._data_out = dict()
        self._step = STEP
        self._color = Color().color
        self._iter = 0
        self._wait = Const.data['STEP_WAIT']
        self._figure = 0
        self._break = 0
        self._life = 5
        super().__init__(self._body[0], self._radius, self._color, all_sprites)
        self.set_data({'key': rnd[random.randint(0, 3)]})

    def update(self):
        # if not self._data:
        #     return
        if self._break == 0:
            cmd = self._data.get('key', [])
            pos = self._data.get('pos', [])
            if pos:
                x, y = self._body[0]
                px, py = pos
                if abs(x - px) > abs(y - py):
                    if x > px:
                        cmd = 'left'
                    else:
                        cmd = 'right'
                else:
                    if y > py:
                        cmd = 'up'
                    else:
                        cmd = 'down'
            if cmd:
                if 'left' in cmd:
                    self._pos[0] = -self._step
                    self._pos[1] = 0
                if 'right' in cmd:
                    self._pos[0] = self._step
                    self._pos[1] = 0
                if 'down' in cmd:
                    self._pos[1] = self._step
                    self._pos[0] = 0
                if 'up' in cmd:
                    self._pos[1] = -self._step
                    self._pos[0] = 0
        else:
            self._break -= 1
        self._data['key'] = None
        self._iter += 1
        if self._iter > self._wait:
            self._iter = 0
            self.move()

    def move(self):
        for i in range(len(self._body)):
            if i == 0:
                segment = self._body[i].copy()
                self._body[i] = [(self._body[i][0] + self._pos[0]) % WIDTH,
                                 (self._body[i][1] + self._pos[1]) % HEIGHT]
                self.move_point(self._body[0])
                # print(self.rect, '|', self._pos, '|', self._body[0])
            else:
                segment, self._body[i] = self._body[i], segment
        self.add_segment(count=self._inc)
        self._inc = 0

    def add_segment(self, count=1, life=0):
        self.set_life(life)
        segment = self._body[-1]
        for _ in range(count):
            self._body.append(segment)
        self.image, self.rect = self.new_radius(max(10, RADIUS + len(self._body) // SIZE_MUL), self._color)
        self.move_point(self._body[0])

    def del_segment(self, count=1):
        for _ in range(min(count, len(self._body) - 1)):
            self._body.pop()
        if self.get_life() > 0:
            self.set_life(-1)

    def set_data(self, data):
        self._data = data

    def get_data(self):
        self._data_out['body'] = self._body
        self._data_out['radius'] = self._radius
        self._data_out['color'] = self._color
        self._data_out['figure'] = self._figure
        self._data_out['length'] = self.get_length()
        self._data_out['life'] = self._life
        to_send = self._data_out.copy()
        self._data_out.clear()
        return to_send

    def get_head(self):
        return self._body[0]

    def get_length(self):
        return len(self._body)

    def get_life(self):
        return self._life

    def set_life(self, delta=0):
        if self._break == 0:
            self._life = max(0, self._life + delta)
        return self._life

    def is_in_head(self, pos):
        px, py = self._body[0]
        h_size = self.get_length() // SIZE_MUL + RADIUS
        ret = abs(pos[0] - px) < h_size and abs(pos[1] - py) < h_size
        return ret

    def eat_in_head(self):
        ret = pygame.sprite.spritecollide(self, eat_sprites, True)
        if ret:
            self._data_out['sound'] = 'eat'
        return ret

    def is_head_to_head(self, player):
        pos = player.get_head()
        size = player.get_length() // SIZE_MUL + self.get_length() // SIZE_MUL + 2 * RADIUS
        delta_x = abs(self._body[0][0] - pos[0]) - size
        delta_y = abs(self._body[0][1] - pos[1]) - size
        if delta_x < 0 and delta_y < 0:
            if self.get_life() == 0 and self.get_length() > 10:
                # self.del_segment(len(self._body))
                self.del_segment(5)
            else:
                self.set_life(-1)
            # player.set_life(-1)
            return True
        return False

    def breake(self):
        if self._break > 0:
            return
        self._pos = [self._pos[0] * -1, self._pos[1] * -1]
        self._break = len(self._body) // 2 + RADIUS
        self._data_out['sound'] = 'break'

    def is_body_atak(self, player):
        start_segment = 1
        if player == self:
            start_segment = MIN_SAFE_LENGTH
        x, y = player.get_head()
        size = player.get_length() // SIZE_MUL + RADIUS
        for i in range(start_segment, self.get_length()):
            sx, sy = self._body[i]
            # print(sx, sy)
            if abs(x - sx) - size < 0 and abs(y - sy) - size < 0:
                cut = self.get_length() - i
                if cut <= player.get_length():
                    self.del_segment(cut)
                    self._data_out['sound'] = 'ataka'
                    player.add_data({'sound': 'ataka'})
                    return cut
                else:
                    return -1
        return 0

    def add_data(self, rec: dict):
        for key, val in rec.items():
            self._data_out[key] = val


class Network:
    def __init__(self):
        self.sound_on = False
        self.clients = []
        self.player_sockets = []
        self.player_data = dict()
        # self.eat_data = []
        self.main_socket = self.init_socket()
        self.game_time = datetime.datetime.now()
        self.common_data = {'HOST': HOST, 'PORT': Const.data['PORT'],
                            'WINNER': ''}
        self.last_winner = ('', 0)
        self.bots_counter = Const.data['BOTS_COUNTER']
        self.game_timer = Const.data['GAME_TIMER']
        # self.step_wait = Const.data['STEP_WAIT']
        self.rect_area = {'game_timer': [pygame.Rect(710, 170, 15, 15), pygame.Rect(790, 170, 20, 15)],
                          'bots_counter': [pygame.Rect(710, 210, 15, 15), pygame.Rect(767, 210, 20, 15)],
                          'step_wait': [pygame.Rect(710, 250, 15, 15), pygame.Rect(760, 250, 20, 15)]
                          }
        self.reset_game()

    def check_click(self, pos):
        def check_area(pos: list[int, int], rect: pygame.Rect):
            return rect.x <= pos[0] <= rect.x +rect.w and rect.y <= pos[1] <= rect.y + rect.h

        if check_area(pos, self.rect_area['bots_counter'][0]):
            self.bots_counter = max(0, self.bots_counter - 1)
        elif check_area(pos, self.rect_area['bots_counter'][1]):
            self.bots_counter = min(20, self.bots_counter + 1)
        elif check_area(pos, self.rect_area['game_timer'][0]):
            self.game_timer = max(10, self.game_timer - 10)
        elif check_area(pos, self.rect_area['game_timer'][1]):
            self.game_timer = min(600, self.game_timer + 10)
        elif check_area(pos, self.rect_area['step_wait'][0]):
            Const.data['STEP_WAIT'] = max(0, Const.data['STEP_WAIT'] - 1)
        elif check_area(pos, self.rect_area['step_wait'][1]):
            Const.data['STEP_WAIT'] = min(15, Const.data['STEP_WAIT'] + 1)

    def prepare_to_send(self):
        data = dict()
        for addr, player in self.player_data.items():
            data[addr] = player.get_data()
        for i, eat in enumerate(eat_sprites):
            data[f'eat{i:03}'] = eat.get_data()
        ret = dict()
        ret['players'] = data
        if self.common_data['WINNER']:
            ret['WINNER'] = self.common_data['WINNER']
            self.common_data['WINNER'] = ''
        timer = self.game_timer - self.get_time_sec()
        ret['TIMER'] = timer
        return ret

    def init_socket(self):
        main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        main_socket.bind((HOST, Const.data['PORT']))
        main_socket.setblocking(False)
        main_socket.listen(1)
        print('Server started at:', HOST, Const.data['PORT'])
        return main_socket

    def init_game(self):
        if datetime.datetime.now() - self.game_time > datetime.timedelta(
                seconds=self.game_timer):
            self.game_time = datetime.datetime.now()
            self.reset_game()

    def get_time_sec(self):
        return (datetime.datetime.now().second + datetime.datetime.now().minute * 60) - (
                self.game_time.second + self.game_time.minute * 60)

    def reset_game(self):
        count = ''
        self.game_time = datetime.datetime.now()
        win_addr, win_len = '', 0
        for addr, player in self.player_data.items():
            if player.get_length() > win_len:
                win_addr = addr
                win_len = player.get_length()
                count = f"{win_addr}. Длина: {win_len}."
                self.last_winner = win_addr, win_len
        self.common_data['WINNER'] = count
        print('Winner:', count)
        print('new game!')
        wins = cur.execute(f"SELECT wins FROM users WHERE TRIM(addr) = '{self.last_winner[0]}'").fetchone()
        # print(wins)
        if wins:
            cur.execute(f"UPDATE users SET wins = {wins[0] + 1} WHERE TRIM(addr) = '{self.last_winner[0]}'")
        con.commit()
        get_sql_stat()
        # print(win_stat)
        self.sound_on = False
        coords.clear()
        for addr in self.player_data.copy():
            if addr[:3] == 'bot':
                self.player_data.pop(addr)
        for i in range(self.bots_counter):
            player = Player()
            player.set_data({'key': 'left'})
            player.add_segment(12)
            self.player_data[f"bot{i:03}"] = player
        for addr in self.player_data.keys():
            if addr[0] != 'b':
                self.player_data[addr] = Player()

    def handle(self, sock: socket.socket) -> any:
        data = None
        try:
            data = sock.recv(DATA_WIND).decode()  # Should be ready
        except ConnectionError:
            print(f"Client suddenly closed while receiving {sock}")
            return None
        except BlockingIOError:
            pass
        except Exception as e:
            print('Receive error:', e)
        return data

    def send_data(self, sock, data):
        try:
            sock.sendall(data)  # Hope it won't block
        except ConnectionError:
            print(f"Client suddenly closed, cannot send")
            return False
        except BlockingIOError:
            pass
        return True


if __name__ == "__main__":
    # fps = FPS
    srv_host = Network()
    texts = [font2.render(f"{hostname} IP: {HOST} PORT: {Const.data['PORT']}",True, 'red'),
             font2.render("Последний победитель:",True, 'green'),
             font2.render('Ботов в игре:', True, 'orange'),
             font2.render('Длина тайма:', True, 'orange'),
             font2.render('Скорость:', True, 'orange')]

    # Игровой цикл
    new_eat_counter = 0
    cicle = True
    while cicle:
        srv_host.init_game()
        try:
            new_socket, addr = srv_host.main_socket.accept()
            addr = addr[0]
            srv_host.main_socket.setblocking(False)
            srv_host.player_sockets.append(new_socket)
            srv_host.player_data[addr] = srv_host.player_data.get(addr, Player())
            print('Connection from:', addr)
            res = cur.execute(f"SELECT * FROM users WHERE TRIM(addr) = '{addr}' ").fetchone()
            if not res:
                cur.execute(f"INSERT INTO users (addr, wins) VALUES ('{addr}', 0)")
                con.commit()
            get_sql_stat()
        except BlockingIOError:
            pass

        # Обработка активности
        # ------------------------------------------------------
        # Игровая механика
        all_sprites.update()
        for addr, player in srv_host.player_data.items():
            for addr2, player2 in srv_host.player_data.items():
                count = player.is_body_atak(player2)
                if count > 0:
                    if addr2 != addr:
                        player2.add_segment(count, 1)
                elif count < 0:
                    player2.breake()
                    continue
                if addr2 == addr:
                    continue
                if player.is_head_to_head(player2):
                    player.breake()
                    continue

        # Проверка поедания корма
        eat_sprites.update()
        for addr, player in srv_host.player_data.items():
            eat = player.eat_in_head()
            if eat:
                player.add_segment()
                break
        if new_eat_counter == COUNT:
            new_eat_counter = 0
            if len(eat_sprites) < EAT_COUNT:
                Eat()
        new_eat_counter += 1

        # Передача данных игрокам
        data = srv_host.prepare_to_send()
        try:
            data = '#####' + json.dumps(data) + '%%%%%'
            data = zlib.compress(data.encode())
            packet_size = len(data)

        except Exception as err:
            print('Error prepare to send:', err)
        for sock in srv_host.player_sockets:
            if not srv_host.send_data(sock, data):
                srv_host.player_sockets.remove(sock)
                sock.close()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cicle = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                srv_host.check_click(event.pos)
            # if event.type == pygame.MOUSEMOTION:
            #     pygame.display.set_caption(f"{event.pos}")

        # Вывод статистики
        screen.fill(pygame.Color((0, 0, 127)))
        text = font.render(f"{'=' * 10} PLAYERS {'=' * 10}", ALIAS, 'yellow')
        screen.blit(text, (45, 50))
        for i, (addr, player) in enumerate(srv_host.player_data.items()):
            color = 'red' if addr == srv_host.last_winner[0] else 'yellow' if addr[:3] != 'bot' else 'gray'
            text = font.render(f"{i + 1:02}: [{addr}] == Life: {player.get_life()}, Len: {player.get_length()}, "
                               f"WINS: {win_stat.get(addr, ' ')}",
                               ALIAS, color)
            screen.blit(text, (45, 70 + i * 25))
        screen.blit(texts[0], (S_WIDTH // 2 - texts[0].get_rect().width // 2, 5))
        screen.blit(texts[1], (460, 400))
        text = font2.render(f"[{srv_host.last_winner[0]}] {srv_host.last_winner[1]}",
                            ALIAS, 'green')
        screen.blit(text, (500, 450))
        game_time = srv_host.game_timer - srv_host.get_time_sec()
        if game_time <= 10 and not srv_host.sound_on:
            srv_host.sound_on = True
            ten_sound.play()
        text = font2.render(f"Timer: {game_time} сек",
                            ALIAS, 'green')
        screen.blit(text, (560, 80))
        screen.blit(texts[2], (500, 200))
        text = font2.render(f"- {srv_host.bots_counter:02} +", ALIAS, 'orange')
        screen.blit(text, (710, 200))
        screen.blit(texts[3], (500, 160))
        text = font2.render(f"- {srv_host.game_timer:03} +", ALIAS, 'orange')
        screen.blit(text, (710,160))
        screen.blit(texts[4], (500, 240))
        text = font2.render(f"- {Const.data['STEP_WAIT']:01} +", ALIAS, 'orange')
        screen.blit(text, (710, 240))
        text = font2.render(f"Размер пакета: {10 * (packet_size // 10)}", ALIAS, 'red')
        screen.blit(text, (500, S_HEIGHT - 50))

        pygame.display.flip()
        s_clock.tick(S_FPS)

        # Получаем данные от игроков
        addr = ''
        for sock in srv_host.player_sockets.copy():
            if 'raddr' not in sock.__repr__():
                continue
            addr = sock.getpeername()
            addr = addr[0]
            data = srv_host.handle(sock)
            if data:
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = dict()
                srv_host.player_data[addr].set_data(data)

    pygame.quit()
    sys.exit()
