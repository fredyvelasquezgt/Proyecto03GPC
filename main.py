import pygame
import sys
from math import cos, sin, pi, atan2
from pygame import mixer

import time

pygame.init()

gray = (119, 118, 110)
red = (255, 0, 0)
black = (0, 0, 0)
green = (0, 200, 0)

techo = (78, 182, 162)
piso = (31, 33, 29)
bright_red = (255, 0, 0)
bright_green = (0, 255, 0)
bright_blue = (0, 0, 255)
blue = (0, 0, 255)
pause = False

display_width = 600
display_height = 600
gamedisplays = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('The Catacomb Abyss')
clock = pygame.time.Clock()

intro_background = pygame.image.load('menu.jpg')
instruction_background = pygame.image.load('menu.jpg')

mixer.music.load('music.mp3')
mixer.music.set_volume(0.8)
mixer.music.play(-1)


def game_loop():
    global pause
    mixer.music.load('music.mp3')
    mixer.music.set_volume(0.3)
    mixer.music.play(-1)
    RAY_AMOUNT = 100
    SPRITE_BACKGROUND = (152, 0, 136, 255)

    wallcolors = {
        '1': pygame.Color('red'),
        '2': pygame.Color('green'),
        '3': pygame.Color('blue'),
        '4': pygame.Color('yellow'),
        '5': pygame.Color('purple')
    }

    wallTextures = {
        '1': pygame.image.load('w.png'),
        '2': pygame.image.load('l.png'),
        '3': pygame.image.load('x.png'),
        '4': pygame.image.load('ww.png'),
        '5': pygame.image.load('bos.png')
    }

    enemies = [{"x": 100,
                "y": 200,
                "sprite": pygame.image.load('boss1.png')},

               {"x": 350,
                "y": 150,
                "sprite": pygame.image.load('boss2.png')},

               {"x": 300,
                "y": 400,
                "sprite": pygame.image.load('boss3.png')}
               ]

    class Raycaster(object):
        def __init__(self, screen):
            self.screen = screen
            _, _, self.width, self.height = screen.get_rect()

            self.map = []
            self.zbuffer = [float('inf') for z in range(self.width)]

            self.blocksize = 50
            self.wallheight = 50

            self.maxdistance = 300

            self.stepSize = 5
            self.turnSize = 5

            self.player = {
                'x': 100,
                'y': 100,
                'fov': 60,
                'angle': 0}

            self.hitEnemy = False

        def load_map(self, filename):
            with open(filename) as file:
                for line in file.readlines():
                    self.map.append(list(line.rstrip()))

        def drawMinimap(self):
            minimapWidth = 100
            minimapHeight = 100

            minimapSurface = pygame.Surface((500, 500))
            minimapSurface.fill(pygame.Color("gray"))

            for x in range(0, 500, self.blocksize):
                for y in range(0, 500, self.blocksize):

                    i = int(x/self.blocksize)
                    j = int(y/self.blocksize)

                    if j < len(self.map):
                        if i < len(self.map[j]):
                            if self.map[j][i] != ' ':
                                tex = wallTextures[self.map[j][i]]
                                tex = pygame.transform.scale(
                                    tex, (self.blocksize, self.blocksize))
                                rect = tex.get_rect()
                                rect = rect.move((x, y))
                                minimapSurface.blit(tex, rect)

            rect = (int(self.player['x'] - 4),
                    int(self.player['y']) - 4, 10, 10)
            minimapSurface.fill(pygame.Color('black'), rect)

            for enemy in enemies:
                rect = (enemy['x'] - 4, enemy['y'] - 4, 10, 10)
                minimapSurface.fill(pygame.Color('red'), rect)

            minimapSurface = pygame.transform.scale(
                minimapSurface, (minimapWidth, minimapHeight))
            self.screen.blit(minimapSurface, (self.width -
                             minimapWidth, self.height - minimapHeight))

        def drawSprite(self, obj, size):
            # Pitagoras
            spriteDist = ((self.player['x'] - obj['x']) **
                          2 + (self.player['y'] - obj['y']) ** 2) ** 0.5

            # Angulo
            spriteAngle = atan2(obj['y'] - self.player['y'],
                                obj['x'] - self.player['x']) * 180 / pi

            # Tamaño del sprite
            aspectRatio = obj['sprite'].get_width() / \
                obj['sprite'].get_height()
            spriteHeight = (self.height / spriteDist) * size
            spriteWidth = spriteHeight * aspectRatio

            # Buscar el punto inicial para dibujar el sprite
            angleDif = (spriteAngle - self.player['angle']) % 360
            angleDif = (angleDif - 360) if angleDif > 180 else angleDif
            startX = angleDif * self.width / self.player['fov']
            startX += (self.width / 2) - (spriteWidth / 2)
            startY = (self.height / 2) - (spriteHeight / 2)
            startX = int(startX)
            startY = int(startY)

            for x in range(startX, startX + int(spriteWidth)):
                if (0 < x < self.width) and self.zbuffer[x] >= spriteDist:
                    for y in range(startY, startY + int(spriteHeight)):
                        tx = int((x - startX) *
                                 obj['sprite'].get_width() / spriteWidth)
                        ty = int((y - startY) *
                                 obj['sprite'].get_height() / spriteHeight)
                        texColor = obj['sprite'].get_at((tx, ty))
                        if texColor != SPRITE_BACKGROUND and texColor[3] > 128:
                            self.screen.set_at((x, y), texColor)

                            if y == self.height / 2:
                                self.zbuffer[x] = spriteDist
                                if x == self.width / 2:
                                    self.hitEnemy = True

        def castRay(self, angle):
            rads = angle * pi / 180
            dist = 0
            stepSize = 1
            stepX = stepSize * cos(rads)
            stepY = stepSize * sin(rads)

            playerPos = (self.player['x'], self.player['y'])

            x = playerPos[0]
            y = playerPos[1]

            while True:
                dist += stepSize

                x += stepX
                y += stepY

                i = int(x/self.blocksize)
                j = int(y/self.blocksize)

                if j < len(self.map):
                    if i < len(self.map[j]):
                        if self.map[j][i] != ' ':

                            hitX = x - i*self.blocksize
                            hitY = y - j*self.blocksize

                            hit = 0

                            if 1 < hitX < self.blocksize-1:
                                if hitY < 1:
                                    hit = self.blocksize - hitX
                                elif hitY >= self.blocksize-1:
                                    hit = hitX
                            elif 1 < hitY < self.blocksize-1:
                                if hitX < 1:
                                    hit = hitY
                                elif hitX >= self.blocksize-1:
                                    hit = self.blocksize - hitY

                            tx = hit / self.blocksize

                            return dist, self.map[j][i], tx

        def render(self):
            halfHeight = int(self.height / 2)

            for column in range(RAY_AMOUNT):
                angle = self.player['angle'] - (self.player['fov'] / 2) + (
                    self.player['fov'] * column / RAY_AMOUNT)
                dist, id, tx = self.castRay(angle)

                rayWidth = int((1 / RAY_AMOUNT) * self.width)

                for i in range(rayWidth):
                    self.zbuffer[column * rayWidth + i] = dist

                startX = int(((column / RAY_AMOUNT) * self.width))

                # perceivedHeight = screenHeight / (distance * cos( rayAngle - viewAngle)) * wallHeight
                h = self.height / \
                    (dist * cos((angle -
                     self.player["angle"]) * pi / 180)) * self.wallheight
                startY = int(halfHeight - h/2)
                endY = int(halfHeight + h/2)

                color_k = (1 - min(1, dist / self.maxdistance)) * 255

                tex = wallTextures[id]
                tex = pygame.transform.scale(
                    tex, (tex.get_width() * rayWidth, int(h)))
                tx = int(tx * tex.get_width())
                self.screen.blit(tex, (startX, startY),
                                 (tx, 0, rayWidth, tex.get_height()))

            self.hitEnemy = False
            for enemy in enemies:
                self.drawSprite(enemy, 50)

            sightRect = (int(self.width / 2 - 2),
                         int(self.height / 2 - 2), 5, 5)
            self.screen.fill(pygame.Color(
                'red') if self.hitEnemy else pygame.Color('white'), sightRect)

            self.drawMinimap()

    width = 600
    height = 600

    pygame.init()
    screen = pygame.display.set_mode(
        (width, height), pygame.DOUBLEBUF | pygame.HWACCEL | pygame.HWSURFACE)
    screen.set_alpha(None)

    rCaster = Raycaster(screen)
    rCaster.load_map("map_f.txt")

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 25)

    def updateFPS():
        fps = str(int(clock.get_fps()))
        fps = font.render(fps, 1, pygame.Color("white"))
        return fps

    isRunning = True
    pasos = mixer.Sound('pasos2.mp3')
    while isRunning:

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                isRunning = False

            elif ev.type == pygame.KEYDOWN:
                newX = rCaster.player['x']
                newY = rCaster.player['y']
                forward = rCaster.player['angle'] * pi / 180
                right = (rCaster.player['angle'] + 90) * pi / 180

                if ev.key == pygame.K_ESCAPE:
                    isRunning = False
                elif ev.key == pygame.K_w:
                    pasos.play()
                    newX += cos(forward) * rCaster.stepSize
                    newY += sin(forward) * rCaster.stepSize
                elif ev.key == pygame.K_s:
                    pasos.play()
                    newX -= cos(forward) * rCaster.stepSize
                    newY -= sin(forward) * rCaster.stepSize
                elif ev.key == pygame.K_a:
                    pasos.play()
                    newX -= cos(right) * rCaster.stepSize
                    newY -= sin(right) * rCaster.stepSize
                elif ev.key == pygame.K_d:
                    pasos.play()
                    newX += cos(right) * rCaster.stepSize
                    newY += sin(right) * rCaster.stepSize
                elif ev.key == pygame.K_q:
                    rCaster.player['angle'] -= rCaster.turnSize
                elif ev.key == pygame.K_e:
                    rCaster.player['angle'] += rCaster.turnSize
                elif ev.key == pygame.K_p:
                    paused()

                i = int(newX/rCaster.blocksize)
                j = int(newY/rCaster.blocksize)

                if rCaster.map[j][i] == ' ':
                    rCaster.player['x'] = newX
                    rCaster.player['y'] = newY

        # Techo
        techo = (78, 182, 162)
        piso = (31, 33, 29)
        screen.fill(pygame.Color(piso),
                    (0, 0,  width, int(height / 2)))

        # Piso

        screen.fill(pygame.Color(techo),
                    (0, int(height / 2),  width, int(height / 2)))

        rCaster.render()

        # FPS
        screen.fill(pygame.Color("black"), (0, 0, 30, 30))
        screen.blit(updateFPS(), (0, 0))
        clock.tick(60)

        button('Pause', 450, 0, 150, 50, techo, piso, "pause")

        pygame.display.flip()

    pygame.quit()
    quit()
    sys.exit()


def text_objects(text, font, color):
    textsurface = font.render(text, True, color)
    return textsurface, textsurface.get_rect()


def introduction():
    introduction = True
    while introduction:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                sys.exit()
        gamedisplays.blit(instruction_background, (0, 0))
        button('', 25, 25, 550, 550, piso, piso, None)
        largetext = pygame.font.Font('freesansbold.ttf', 80)
        smalltext = pygame.font.Font('freesansbold.ttf', 20)
        mediumtext = pygame.font.Font('freesansbold.ttf', 40)

        TextSurf, TextRect = text_objects('CONTROLES', mediumtext, techo)
        TextRect.center = ((300), (80))
        gamedisplays.blit(TextSurf, TextRect)
        ptextSurf, ptextRect = text_objects('P : PAUSA', smalltext, techo)
        ptextRect.center = ((200), (150))

        stextSurf, stextRect = text_objects('W : Adelante', smalltext, techo)
        stextRect.center = ((200), (200))
        htextSurf, hTextRect = text_objects('A : IZQUIERDA', smalltext, techo)
        hTextRect.center = ((200), (250))
        atextSurf, atextRect = text_objects('S : ATRAS', smalltext, techo)
        atextRect.center = ((200), (300))
        rtextSurf, rTextRect = text_objects('D : DERECHA', smalltext, techo)
        rTextRect.center = ((200), (350))
        q_btn, q_btn_r = text_objects('Q : GIRAR IZQUIERDA', smalltext, techo)
        q_btn_r.center = ((200), (400))
        gamedisplays.blit(q_btn, q_btn_r)
        e_btn, e_btn_r = text_objects('E : GIRAR DERECHA', smalltext, techo)
        e_btn_r.center = ((200), (450))
        gamedisplays.blit(e_btn, e_btn_r)
        gamedisplays.blit(stextSurf, stextRect)
        gamedisplays.blit(htextSurf, hTextRect)
        gamedisplays.blit(atextSurf, atextRect)
        gamedisplays.blit(rtextSurf, rTextRect)
        gamedisplays.blit(ptextSurf, ptextRect)
        button("ATRAS", 250, 500, 100, 50, techo, piso, 'inicio')

        pygame.display.update()
        clock.tick(30)


def intro_loop():
    introduction = True

    while introduction:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                sys.exit()
        gamedisplays.blit(instruction_background, (0, 0))

        # largetext = pygame.font.Font('freesansbold.ttf', 80)
        # smalltext = pygame.font.Font('freesansbold.ttf', 20)
        # mediumtext = pygame.font.Font('freesansbold.ttf', 40)

        # TextSurf, TextRect = text_objects('CONTROLES', mediumtext, techo)
        # TextRect.center = ((300), (80))
        # gamedisplays.blit(TextSurf, TextRect)
        # ptextSurf, ptextRect = text_objects('P : PAUSA', smalltext, techo)
        # ptextRect.center = ((200), (150))

        # stextSurf, stextRect = text_objects('W : Adelante', smalltext, techo)
        # stextRect.center = ((200), (200))
        # htextSurf, hTextRect = text_objects('A : IZQUIERDA', smalltext, techo)
        # hTextRect.center = ((200), (250))
        # atextSurf, atextRect = text_objects('S : ATRAS', smalltext, techo)
        # atextRect.center = ((200), (300))
        # rtextSurf, rTextRect = text_objects('D : DERECHA', smalltext, techo)
        # rTextRect.center = ((200), (350))
        # q_btn, q_btn_r = text_objects('Q : GIRAR IZQUIERDA', smalltext, techo)
        # q_btn_r.center = ((200), (400))
        # gamedisplays.blit(q_btn, q_btn_r)
        # e_btn, e_btn_r = text_objects('E : GIRAR DERECHA', smalltext, techo)
        # e_btn_r.center = ((200), (450))
        # gamedisplays.blit(e_btn, e_btn_r)
        # gamedisplays.blit(stextSurf, stextRect)
        # gamedisplays.blit(htextSurf, hTextRect)
        # gamedisplays.blit(atextSurf, atextRect)
        # gamedisplays.blit(rtextSurf, rTextRect)
        # gamedisplays.blit(ptextSurf, ptextRect)
        button("INICIO", 200, 300, 100, 50, techo, piso, 'play')
        button("SALIR", 200, 500, 100, 50, techo, piso, 'quit')
        button("CONTROLES", 200, 400, 100, 50, techo, piso, 'intro')
        # button('INICIO', 200, 300, 200, 50, techo, piso, 'play')
        # button('SALIR', 200, 500, 200, 50, techo, piso, 'quit')
        # button('CONTROLES', 200, 400, 200, 50, techo, piso, 'intro')

        pygame.display.update()
        clock.tick(30)


def paused():
    global pause
    pause = True

    while pause:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                sys.exit()
        gamedisplays.blit(intro_background, (0, 0))
        mediumtext = pygame.font.Font('freesansbold.ttf', 40)
        button('', 25, 25, 550, 550, piso, piso, None)
        title_pause, title_pause_r = text_objects("PAUSA", mediumtext, techo)
        title_pause_r.center = ((display_width//2), (display_height//2))
        gamedisplays.blit(title_pause, title_pause_r)
        button("CONTINUAR", 25, 400, 150, 50, techo, piso, 'resume')
        button("REINICIAR", 225, 400, 150, 50, techo, piso, 'play')
        button("MENU", 425, 400, 150, 50, techo, piso, 'inicio')
        pygame.display.update()
        clock.tick(30)


def resume():
    global pause
    pause = False


def button(msg, x, y, w, h, ic, ac, action=None):
    selected = mixer.Sound('click.wav')
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x+w > mouse[0] > x and y+h > mouse[1] > y:
        pygame.draw.rect(gamedisplays, ac, (x, y, w, h))
        if click[0] == 1 and action != None:
            if action == 'play':
                selected.play()
                game_loop()

            if action == 'intro':
                selected.play()
                introduction()
            if action == 'inicio':
                selected.play()

                intro_loop()
            if action == 'pause':
                selected.play()
                paused()
            if action == 'resume':
                selected.play()
                resume()
            if action == 'quit':
                selected.play()
                pygame.quit()
                quit()
                sys.exit()

    else:
        pygame.draw.rect(gamedisplays, ic, (x, y, w, h))
    smalltext = pygame.font.Font('freesansbold.ttf', 20)
    textsurf, textrect = text_objects(msg, smalltext, black)
    textrect.center = ((x+(w/2)), (y+(h/2)))
    gamedisplays.blit(textsurf, textrect)


intro_loop()
