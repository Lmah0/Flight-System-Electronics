
import RPi.GPIO as GPIO
from time import sleep
from math import ceil
GPIO.setwarnings(False)

#GENERAL SETUP------------------------------------------------------------------

CW = 1           #Clockwise val
CCW = 0          #CounterClockwise val
SPR = 200        #Steps per revolutions
delay = 1/3000   #Generic delay (Lower for faster spin) (1/3000 is a pretty good speed)
diam = 0.03      #diameter of spool in meters      

#MOTOR 1 SETUP

DIR1 = 27       #Direction pin of motor 1
STEP1 = 17      #Step pin of motor 1

#MOTOR 2 SETUP

DIR2 = 24
STEP2 = 23

#GPIO ALL MOTORS SETUP

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)    #Set DIR1 pin as output 
GPIO.setup(STEP1, GPIO.OUT)   #Set STEP1 pin as output
GPIO.setup(DIR2, GPIO.OUT)    #Set DIR2 pin as output 
GPIO.setup(STEP2, GPIO.OUT)   #Set STEP2 pin as output                                

#Main Script--------------------------------------------------------------------

def relay1(rot, spin):              #RELAY CLOCKWISE MEANS RELAY up
  GPIO.output(DIR1, spin)           #Set direction to SPIN (CW OR CCW)
  rot = rot/(diam*3.1415926)        #Convert meter input to rotations
  for x in range(ceil(SPR * rot)):

    y = x/(SPR*rot)                 #Y is the percentage through the movement
    damping = 4*(y-0.5)**2 + 1      #smoothing formula
    GPIO.output(STEP1, GPIO.HIGH)   #MOVEMENT SCRIPT
    sleep(delay*damping)
    GPIO.output(STEP1, GPIO.LOW)
    sleep(delay*damping)
    

def relay2(rot, spin):              #RELAY CLOCKWISE MEANS RELAY up
  GPIO.output(DIR2, spin)           #Set direction to SPIN (CW OR CCW)
  rot = rot/(diam*3.1415926)        #Convert meter input to rotations
  for x in range(ceil(SPR * rot)):

    y = x/(SPR*rot)                 # Y is the percentage through the movement
    damping = 4*(y-0.5)**2 + 1      # smoothing formula
    GPIO.output(STEP2, GPIO.HIGH)   #MOVEMENT SCRIPT
    sleep(delay*damping)
    GPIO.output(STEP2, GPIO.LOW)
    sleep(delay*damping)

#MOTOR TEST---------------------------------------------------------------
for x in range(1):
  #relay1(4, CW) ------ motor 1 off
  #sleep(1)
  relay2(1, CW)
  sleep(1)