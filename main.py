
import random
import pygame
import sys
from pygame.locals import *
import smbus
import math
import time
import threading
Snakespeed = 6
Window_Width = 800
Window_Height = 500
Cell_Size = 20  # Width and height of the cells  
# Ensuring that the cells fit perfectly in the window. eg if cell size was  
# 10     and window width or windowheight were 15 only 1.5 cells would  
# fit.      
assert Window_Width % Cell_Size == 0, "Window width must be a multiple of cell size."
# Ensuring that only whole integer number of cells fit perfectly in the window.  
assert Window_Height % Cell_Size == 0, "Window height must be a multiple of cell size."
Cell_W = int(Window_Width / Cell_Size)  # Cell Width  
Cell_H = int(Window_Height / Cell_Size)  # Cellc Height  

White = (255, 255, 255)
Black = (0, 0, 0)
Red = (255, 0, 0)  # Defining element colors for the program.  
Green = (0, 255, 0)
DARKGreen = (0, 155, 0)
DARKGRAY = (40, 40, 40)
YELLOW = (255, 255, 0)
Red_DARK = (150, 0, 0)
BLUE = (0, 0, 255)
BLUE_DARK = (0, 0, 150)

BGCOLOR = Black  # Background color

UP = 'up'
DOWN = 'down'  # Defining keyboard keys.
LEFT = 'left'
RIGHT = 'right'

HEAD = 0  # Syntactic sugar: index of the snake's head  

global accdata


def main():
    global SnakespeedCLOCK, DISPLAYSURF, BASICFONT

    pygame.init()
    SnakespeedCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((Window_Width, Window_Height))
    BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
    pygame.display.set_caption('Snake')

    showStartScreen()
    while True:
        runGame()
        showGameOverScreen()

class acc():
    def __init__(self):
        self.name="accelerator data"
        self.power_mgmt_1 = 0x6b
        self.power_mgmt_2 = 0x6c
        self.bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards
        self.address = 0x68       # This is the address value read via the i2cdetect command
        self.bus.write_byte_data(self.address, self.power_mgmt_1, 0)
        self.x_bias,self.y_bias=self.get_bias_x_y()
        self.direction_detected=0
        self.v_direction_detected=0
        self.vx=0
        self.vy=0
        self.dt=0.001
        self.a_bias_after_bias=0.03
        self.v_damp_rate=0.991
        self.v_bias_after_bias=0.0005 #Least detected velocity/9.8 m/s, less and more senstive
        self.v_last_direction=''
        self.v_direction=''
        self.v_direction_show=0
        self.sx=0
        self.sy=0
        self.direction_pre=1
        
        self.t_last=round(time.time(),4)
        self.t_now=round(time.time(),4)
        
        self.go_main_loop=threading.Thread(target=self.main_loop,args=())
        self.go_main_loop.start()
    def main_loop(self) :
        while(1):
            #self.t_last=self.t_now
            #self.t_now=round(time.time(),6)
            #print(self.t_now)
            time.sleep(self.dt)
            #self.dt=self.t_now-self.t_last
            self.update_vx_vy()
            self.v_direction_detected=0
            self.update_vx_vy_direction()
            self.update_v_direction_show()
            #self.update_sx_sy()
            if(self.v_direction_show):
                print(self.v_direction)
                print(self.vx,self.vy)
            #print(self.get_x_y_direction())
                
    def update_sx_sy(self):
        dt=self.dt
        self.sx+=self.vx*dt
        self.sy+=self.vy*dt
        if(random.random()<dt):
            print('x,y=',self.sx*9.8*100,self.sy*9.8*100)
    def update_v_direction_show(self):
        if(self.v_direction==self.v_last_direction):
            self.v_direction_show=0
        else:
            self.v_direction_show=1
    def get_x_y_correct(self):
        x_co,y_co=self.get_x_y_raw()
        x_co-=self.x_bias
        y_co-=self.y_bias
        #print(x_co,y_co)
        return x_co,y_co
    def check_v_direction_inline(self):
        if(self.v_last_direction=='left' and self.v_direction=='right'):
            self.v_direction=self.v_last_direction
        if(self.v_last_direction=='right' and self.v_direction=='left'):
            self.v_direction=self.v_last_direction
        if(self.v_last_direction=='up' and self.v_direction=='down'):
            self.v_direction=self.v_last_direction
        if(self.v_last_direction=='down' and self.v_direction=='up'):
            self.v_direction=self.v_last_direction
        
            
    def update_vx_vy_direction(self):
        vx,vy=self.vx,self.vy
        self.v_last_direction=self.v_direction
        if(abs(vx)>self.v_bias_after_bias or abs(vy)>self.v_bias_after_bias):
            if(abs(vx)>self.direction_pre*abs(vy)):
                self.v_direction_detected=1
                if(vx>0):
                    self.v_direction="right"
                else:
                    self.v_direction="left"
            elif(abs(vy)>self.direction_pre*abs(vx)):
                self.v_direction_detected=1
                if(vy>0):
                    self.v_direction="up"
                else:
                    self.v_direction='down'
            else:
                return 0
            #self.check_v_direction_inline()
            return self.v_direction
        else:
            return 0
        
    def update_vx_vy(self):
        ax,ay=self.get_x_y_correct()
        self.vx+=ax*self.dt
        self.vy+=ay*self.dt
        if(random.random()<0.01):
            print(self.vx,self.vy)
        self.vx=self.vx*self.v_damp_rate
        self.vy=self.vy*self.v_damp_rate
        #print(self.vx,self.vy)
        
    def get_ax_ay_direction(self): #up 1 down 2 left 3 right 4
        x,y=self.get_x_y_correct()
        bias_after_bias=0.03
        if(abs(x)>bias_after_bias or abs(y)>bias_after_bias):
            if(abs(x)>abs(y)):
                if(x>0):
                    return "right"
                else:
                    return "left"
            else:
                if(y>0):
                    return "up"
                else:
                    return 'down'
            self.direction_detected=1
        else:
            return 0
    def get_x_y_raw(self):
        accel_xout = self.read_word_2c(0x3b)
        accel_yout = self.read_word_2c(0x3d)
        accel_zout = self.read_word_2c(0x3f)
        accel_xout_scaled = accel_xout / 16384.0
        accel_yout_scaled = accel_yout / 16384.0
        accel_zout_scaled = accel_zout / 16384.0
        #print ("accel_xout: ", accel_xout, " scaled: ", accel_xout_scaled)
        #print ("accel_yout: ", accel_yout, " scaled: ", accel_yout_scaled)
        #print ("accel_zout: ", accel_zout, " scaled: ", accel_zout_scaled)
        return accel_xout_scaled,accel_yout_scaled
    def get_bias_x_y(self):
        sample_times=1000
        
        x_sum=0
        y_sum=0
        n=0
        while(n<sample_times):
            x,y=self.get_x_y_raw()
            x_sum+=x
            y_sum+=y
            n+=1
        x_bias=x_sum/sample_times
        y_bias=y_sum/sample_times
        #print(x_bias,y_bias)
        print('calib finished')
        return(x_bias,y_bias)
        
    def read_byte(self,adr):
        return self.bus.read_byte_data(self.address, adr)

    def read_word(self,adr):
        high = self.bus.read_byte_data(self.address, adr)
        low = self.bus.read_byte_data(self.address, adr+1)
        val = (high << 8) + low
        return val
    def read_word_2c(self,adr):
        val = self.read_word(adr)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val
    def dist(self,a,b):
        return math.sqrt((a*a)+(b*b))

    def get_y_rotation(self,x,y,z):
        radians = math.atan2(x, dist(y,z))
        return -math.degrees(radians)

    def get_x_rotation(self,x,y,z):
        radians = math.atan2(y, dist(x,z))
        return math.degrees(radians)
class rasp():
    def get_cmd():#up,down,left,right
        #cmd_list=['up','down','left','right']
        global accdata
        return accdata.v_direction
    def get_rasp_status():
        global accdata
        return 1
def runGame():
    # Set a random start point.
    startx = random.randint(5, Cell_W - 6)
    starty = random.randint(5, Cell_H - 6)
    wormCoords = [{'x': startx, 'y': starty},
                  {'x': startx - 1, 'y': starty},
                  {'x': startx - 2, 'y': starty}]
    direction = RIGHT

    # Start the apple in a random place.  
    apple = getRandomLocation()

    while True:  # main game loop#print('.',end='')
        for event in pygame.event.get():  # event handling loop

            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if (event.key == K_LEFT) and direction != RIGHT:
                    direction = LEFT
                elif (event.key == K_RIGHT) and direction != LEFT:
                    direction = RIGHT
                elif (event.key == K_UP) and direction != DOWN:
                    direction = UP
                elif (event.key == K_DOWN) and direction != UP:
                    direction = DOWN
                elif event.key == K_ESCAPE:
                    print('key escape detected')
                    terminate()

                    # check if the Snake has hit itself or the edge
        if(rasp.get_rasp_status()):
            cmd=rasp.get_cmd()
            if (cmd == LEFT) and direction != RIGHT:
                    direction = LEFT
            elif (cmd== RIGHT) and direction != LEFT:
                    direction = RIGHT
            elif (cmd == UP) and direction != DOWN:
                    direction = UP
            elif (cmd== DOWN) and direction != UP:
                    direction = DOWN
        if wormCoords[HEAD]['x'] == -1 or wormCoords[HEAD]['x'] == Cell_W or wormCoords[HEAD]['y'] == -1 or \
                wormCoords[HEAD]['y'] == Cell_H:
            return  # game over  
        for wormBody in wormCoords[1:]:
            if wormBody['x'] == wormCoords[HEAD]['x'] and wormBody['y'] == wormCoords[HEAD]['y']:
                return  # game over  

        # check if Snake has eaten an apply  
        if wormCoords[HEAD]['x'] == apple['x'] and wormCoords[HEAD]['y'] == apple['y']:
            # don't remove worm's tail segment  
            apple = getRandomLocation()  # set a new apple somewhere  
        else:
            del wormCoords[-1]  # remove worm's tail segment  

        # move the worm by adding a segment in the direction it is moving  
        if direction == UP:
            newHead = {'x': wormCoords[HEAD]['x'],
                       'y': wormCoords[HEAD]['y'] - 1}
        elif direction == DOWN:
            newHead = {'x': wormCoords[HEAD]['x'],
                       'y': wormCoords[HEAD]['y'] + 1}
        elif direction == LEFT:
            newHead = {'x': wormCoords[HEAD][
                                'x'] - 1, 'y': wormCoords[HEAD]['y']}
        elif direction == RIGHT:
            newHead = {'x': wormCoords[HEAD][
                                'x'] + 1, 'y': wormCoords[HEAD]['y']}
        wormCoords.insert(0, newHead)
        DISPLAYSURF.fill(BGCOLOR)
        drawGrid()
        drawWorm(wormCoords)
        drawApple(apple)
        drawScore(len(wormCoords) - 3)
        pygame.display.update()
        SnakespeedCLOCK.tick(Snakespeed)


def drawPressKeyMsg():
    pressKeySurf = BASICFONT.render('Press a key to play.', True, White)
    pressKeyRect = pressKeySurf.get_rect()
    pressKeyRect.topleft = (Window_Width - 200, Window_Height - 30)
    DISPLAYSURF.blit(pressKeySurf, pressKeyRect)


def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()
    keyUpEvents = pygame.event.get(KEYUP)

    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key


def showStartScreen():
    titleFont = pygame.font.Font('freesansbold.ttf', 100)
    titleSurf1 = titleFont.render('Snake!', True, White, DARKGreen)
    degrees1 = 0
    degrees2 = 0
    while True:
        DISPLAYSURF.fill(BGCOLOR)
        rotatedSurf1 = pygame.transform.rotate(titleSurf1, degrees1)
        rotatedRect1 = rotatedSurf1.get_rect()
        rotatedRect1.center = (Window_Width / 2, Window_Height / 2)
        DISPLAYSURF.blit(rotatedSurf1, rotatedRect1)

        drawPressKeyMsg()

        if checkForKeyPress():
            pygame.event.get()  # clear event queue  
            return
        pygame.display.update()
        SnakespeedCLOCK.tick(Snakespeed)
        degrees1 += 3  # rotate by 3 degrees each frame  
        degrees2 += 7  # rotate by 7 degrees each frame  


def terminate():
    pygame.quit()
    sys.exit()


def getRandomLocation():
    return {'x': random.randint(0, Cell_W - 1), 'y': random.randint(0, Cell_H - 1)}


def showGameOverScreen():
    gameOverFont = pygame.font.Font('freesansbold.ttf', 100)
    gameSurf = gameOverFont.render('Game', True, White)
    overSurf = gameOverFont.render('Over', True, White)
    gameRect = gameSurf.get_rect()
    overRect = overSurf.get_rect()
    gameRect.midtop = (Window_Width / 2, 10)
    overRect.midtop = (Window_Width / 2, gameRect.height + 10 + 25)

    DISPLAYSURF.blit(gameSurf, gameRect)
    DISPLAYSURF.blit(overSurf, overRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500)
    checkForKeyPress()  # clear out any key presses in the event queue  

    while True:
        if checkForKeyPress():
            pygame.event.get()  # clear event queue  
            return


def drawScore(score):
    scoreSurf = BASICFONT.render('Score: %s' % (score), True, White)
    scoreRect = scoreSurf.get_rect()
    scoreRect.topleft = (Window_Width - 120, 10)
    DISPLAYSURF.blit(scoreSurf, scoreRect)


def drawWorm(wormCoords):
    for coord in wormCoords:
        x = coord['x'] * Cell_Size
        y = coord['y'] * Cell_Size
        wormSegmentRect = pygame.Rect(x, y, Cell_Size, Cell_Size)
        pygame.draw.rect(DISPLAYSURF, DARKGreen, wormSegmentRect)
        wormInnerSegmentRect = pygame.Rect(
            x + 4, y + 4, Cell_Size - 8, Cell_Size - 8)
        pygame.draw.rect(DISPLAYSURF, Green, wormInnerSegmentRect)


def drawApple(coord):
    x = coord['x'] * Cell_Size
    y = coord['y'] * Cell_Size
    appleRect = pygame.Rect(x, y, Cell_Size, Cell_Size)
    pygame.draw.rect(DISPLAYSURF, Red, appleRect)


def drawGrid():
    for x in range(0, Window_Width, Cell_Size):  # draw vertical lines  
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (x, 0), (x, Window_Height))
    for y in range(0, Window_Height, Cell_Size):  # draw horizontal lines  
        pygame.draw.line(DISPLAYSURF, DARKGRAY, (0, y), (Window_Width, y))


if __name__ == '__main__':
    try:
        
        print('start')
        accdata=acc()
        
        main()
        #acc()
        print('end')
        while(1):
            pass
    except SystemExit:
        pass  
