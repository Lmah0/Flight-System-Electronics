import RPi.GPIO as GPIO
from time import sleep
GPIO.setwarnings(False)

#GENERAL SETUP------------------------------------------------------------------

CW = 1           #Clockwise val
CCW = 0          #CounterClockwise val
SPR = 200        #Steps per revolutions
delay = 1/2000    #Generic delay (Lower for faster spin) (1500 is pre good)

#MOTOR 1 SETUP

DIR1 = 27    #Direction pin of motor 1
STEP1 = 17   #Step pin of motor 1

#GPIO ALL MOTORS SETUP

GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR1, GPIO.OUT)    #Set DIR1 pin as output 
GPIO.setup(STEP1, GPIO.OUT)   #Set STEP1 pin as output

#Main Script--------------------------------------------------------------------

def relay1(rot, spin):              #RELAY CLOCKWISE MEANS RELAY DOWN
  GPIO.output(DIR1, spin)                 #Set direction to SPIN (CW OR CCW)
  for x in range(SPR * rot):

    y = x/(SPR*rot)                # Y is the percentage through the movement
    damping = 4*(y-0.5)**2 + 1     # smoothing formula
    
    GPIO.output(STEP1, GPIO.HIGH)  #MOVEMENT SCRIPT
    sleep(delay*damping)
    GPIO.output(STEP1, GPIO.LOW)
    sleep(delay*damping)

#SPIN UP THEN DOWN
for x in range(2):
  relay1(10, CCW)
  sleep(1)
  
  relay1(10, CW)
  sleep(1)

#NOTES--------------------------------------------------------------------------
# -modify the for loop to emulate acceleration
# -incorporate for loop into a function that allows user
#  to pick the exact motor, pick direction, amount of rotations
# -

