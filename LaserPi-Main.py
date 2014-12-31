#!/usr/bin/python

import sys,tty,termios
import RPi.GPIO as GPIO
import time
import random
import argparse
import pickle
import os.path
import threading
import sys
from shapely.geometry import Polygon, Point
from Adafruit_PWM_Servo_Driver import PWM

#Random Polygon point log (Comment out to disable logging)
#polylog = "polygon.log"

#File where polygon points will be stored for random operation
polygonConfFile = 'polygondict.conf'

# Set twitch status at startup
twitch = False
#Multiplier that twitch routine starts with.  Higher number = more twitchy
twitchX = 1
twitchMin = 0.25
twitchMax = 4
twitchStep = 0.25

#Azi servo limits
##Lower numbers = farther right as the device faces
azirightlimit = 280
azileftlimit = 560
##Determine Azi servo center and set servo start point
aziCenter = int(((azileftlimit - azirightlimit) / 2) + azirightlimit)
aziservo = aziCenter + 1 

#Alt servo limits
##Lower number = lower altitude
alttoplimit = 250
altbottomlimit = 560
##Determine Alt servo center and set servo start point
altCenter = int(((altbottomlimit - alttoplimit) / 2) + alttoplimit)
altservo = altCenter + 1 

########################
#Verbose logging stuff
parser = argparse.ArgumentParser(
		description='A script to help exercise your cats by James Sutherland -- k7huw@k7huw.com'
)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
		action="store_true", dest="verbose", default=False,
)
cmdargs = parser.parse_args()

# Initialise the PWM board using the default address with (or wihtout) debug
if cmdargs.verbose:
	#pwm = PWM(0x40, debug=True)
	pwm = PWM(0x40, debug=False)
else:
	pwm = PWM(0x40, debug=False)

# Uncomment this and the "with print_lock" statements below to insure output to the screen
#   is sequential.  Not needed at this point so no reason to lock the threads.
#print_lock = threading.Lock()
def vprint(*vbargs):
		if cmdargs.verbose:
			#with print_lock:
				for vbarg in vbargs:
					sys.stdout.write(str(vbarg) + " ")
				sys.stdout.write("\r\n")

########################
#Safe printing from inside threads
# Keeps crazy formatting from happening.  Random spaces all over the place. 
# This keeps things looking tidy on output.
def safe_print(*spargs):
	#with print_lock:
		for sparg in spargs:
				sys.stdout.write(str(sparg) + " ")
		sys.stdout.write("\r\n")

########################
#Setup the GPIO Pins
pwm.setPWMFreq(60)
GPIO.setmode(GPIO.BCM)
#Laser Switch
GPIO.setup(26, GPIO.OUT)
#Touch Switch
GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

########################

#Message that gets printed when you hit the wrong key
helpmsg = "Use a, s, d, f, c, l, R, or Q to quit"

####### Setup Threads

#When this goes true all the threads stop
exitflag = False

#Thread that deals with Azimith Servo
class aziThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		vprint("Starting " + self.name)
		moveazi()
		vprint("Exiting " + self.name)

#Thread that deals with Altitude Servo
class altThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		vprint("Starting " + self.name)
		movealt()
		vprint("Exiting " + self.name)

#Thread that does the servo twitch
class TwitchThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		vprint("Starting " + self.name)
		twitchy()
		vprint("Exiting " + self.name)

####### Functions that threads use

#Function that moves the azi servo, runs in it's own thread
def moveazi():
	global aziservo
	aziCurrent = aziCenter
	while not exitflag:
		if twitch:
			aziservocommand = azitwitch
		else:
			aziservocommand = aziservo
		if aziservocommand != aziCurrent:
			if aziservocommand < azirightlimit:
				aziservocommand = azirightlimit
				aziservo = aziservocommand
				vprint("Aziservo hit right limit")
			elif aziservocommand > azileftlimit:
				aziservocommand = azileftlimit
				aziservo = aziservocommand
				vprint("Aziservo hit left limit")
			else:
				vprint("Setting Azi servo to:",aziservo)
				pwm.setPWM(0, 0, int(aziservocommand))
				aziCurrent = aziservocommand
		time.sleep(0.01)

#Function that moves the alt servo, runs in it's own thread
def movealt():
	global altservo
	altCurrent = altCenter
	while not exitflag:
		if twitch:
			altservocommand = alttwitch
		else:
			altservocommand = altservo
		if altservocommand != altCurrent:
			if altservocommand < alttoplimit:
				altservocommand = alttoplimit
				altservo = altservocommand
				vprint("Altservo hit top limit")
			elif altservocommand > altbottomlimit:
				altservocommand = altbottomlimit
				altservo = altservocommand
				vprint("Altservo hit bottom limit")
			else:
				vprint("Setting Alt servo to:",altservo)
				pwm.setPWM(1, 0, int(altservocommand))
				altCurrent = altservocommand
		time.sleep(0.01)

#Function that twitches the servos, runs in it's own thread
## altservo & aziservo = Servo position commanded by human (or by servo mover threads if we are near
##                       the servo limits)
## alttwitch & azitwitch = Servo position commanded by twitch.  Obeyed by the servo mover threads
##       		   only if twitch is True.
## altwant & aziwant = The posstion the servos where in when the latest round of twitching started.
##   		       We will return to the want posstions at the end of every twitch cycle so that
##                     the servos don't wander too far.
def twitchy():
	global alttwitch,azitwitch
	twitchcount = 0
	while not exitflag:
		if not 'aziwant' in locals() or \
		   not 'altwant' in locals() or \
		   not 'azitwitch' in globals() or \
		   not 'alttwitch' in globals():
			vprint ("One of the twitch variables we need don't exist so we're setting them up.")
			aziwant = aziservo
			altwant = altservo
			azitwitch = aziservo
			alttwitch = altservo
		if twitch == True:	
			if aziwant != aziservo or altwant != altservo:
				vprint("Commanded servo position changed during twitch.")
				azitwitch = aziservo
				aziwant = aziservo
				alttwitch = altservo
				altwant = altservo
			else:
				if laserstatus == False:
					azitwitch = aziservo
					alttwitch = altservo
				elif twitchcount < 10:
					lrtwitch = random.randint(0,2)
					if lrtwitch == 0:
							azitwitch = azitwitch + (random.randint(0,3) * twitchX)
					elif lrtwitch == 2:
							azitwitch = azitwitch - (random.randint(0,3) * twitchX)
					udtwitch = random.randint(0,2)
					if udtwitch == 0:
						alttwitch = alttwitch + (random.randint(0,3) * twitchX)
					elif udtwitch == 2:
						alttwitch = alttwitch - (random.randint(0,3) * twitchX)
					twitchcount = twitchcount + 1
				elif twitchcount >= 10:
					vprint("twitch count reached driving back to alt:",altwant,"azi:",aziwant)
					twitchcount = 0
					alttwitch = altwant
					azitwitch = aziwant
		#time.sleep(random.uniform(0.1,0.8))
		time.sleep(0.1)

####### Other Functions

class _Getch:
	def __call__(self):
			fd = sys.stdin.fileno()
			old_settings = termios.tcgetattr(fd)
			try:
				tty.setraw(sys.stdin.fileno())
				ch = sys.stdin.read(1)
			finally:
				termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
			return ch

def get_bounds_of_polygon():
	global minazi,maxazi,minalt,maxalt,polygon
	vprint("Finding bounds of polygon")
	vprint("Polygon Dictionary:",polygondict)
	polygon = Polygon([(polygondict['Aazi'], polygondict['Aalt']), (polygondict['Bazi'], polygondict['Balt']), (polygondict['Cazi'], polygondict['Calt']), (polygondict['Dazi'], polygondict['Dalt'])])

	# Write bounds to log file
	if 'polylog' in globals():
		with open(polylog, "a") as mypolylog:
			mypolylog.write("Polygon: %s\n" % polygon)

	# Seperate bounds from tuple into seperate variables
	(minazi, minalt, maxazi, maxalt) = polygon.bounds
	vprint("	minazi",minazi)
	vprint("	maxazi",maxazi)
	vprint("	minalt",minalt)
	vprint("	maxalt",maxalt)

	# Write bounds to log file
	if 'polylog' in globals():
		with open(polylog, "a") as mypolylog:
			mypolylog.write("Polygon bounds: minazi %s, maxazi %s, minalt %s, maxalt %s\n" % (minazi, maxazi, minalt, maxalt))

def get_random_point_in_polygon():
		INVALID_X = -9999
		INVALID_Y = -9999
		p = Point(INVALID_X, INVALID_Y)
		while not polygon.contains(p):
			vprint("Finding random point inside polygon")
			p_azi = random.uniform(minazi, maxazi)
			vprint("	Random Azi:",p_azi)
			p_alt = random.uniform(minalt, maxalt)
			vprint("	Random Azi:",p_alt)
			p = Point(p_azi, p_alt)
		vprint("	ACCEPTED PAIR: azi:",p_azi,"alt:",p_alt)
		if 'polylog' in globals():
			with open(polylog, "a") as mypolylog:
				mypolylog.write("Points: azi %s, alt %s\n" % (p_azi, p_alt))
		return p_azi,p_alt

# Each time this is run the laser will change states (off or on)
def laser(switch):
	global laserstatus
	if switch == "on":
		laserstatus = True
		vprint("Laser switched on")
	elif switch == "off":
		laserstatus = False
		vprint("Laser switched off")
	elif switch == "toggle":
		if laserstatus == False:
			laserstatus = True
			vprint("Laser power toggled to on")
		else:
			laserstatus = False
			vprint("Laser power toggled to off")
	GPIO.output(26, laserstatus)

def LoadRandomArea():
	vprint("Load Random Area")
	global polygondict
	# Check to see if it's already loaded and if so do nothing
	if 'polygondict' not in globals():
		if os.path.isfile(polygonConfFile) == True:
			with open(polygonConfFile, 'rb') as handle:
				polygondict = pickle.loads(handle.read())
		else:
			polygondict = {'BlankHolder':0}
	vprint("	",polygondict)

def PrintRandomArea():
	global altservo,aziservo
	vprint("Print Random Area")
	LoadRandomArea()
	if 'Aalt' in polygondict:
		safe_print("Point A - Alt:",polygondict['Aalt'],"Azi:",polygondict['Aazi'])
		altservo = polygondict['Aalt']
		aziservo = polygondict['Aazi']
		time.sleep(1)
	else:
		safe_print("Point A - not defined")
	if 'Balt' in polygondict:
		safe_print("Point B - Alt:",polygondict['Balt'],"Azi:",polygondict['Bazi'])
		altservo = polygondict['Balt']
		aziservo = polygondict['Bazi']
		time.sleep(1)
	else:
		safe_print("Point B - not defined")
	if 'Calt' in polygondict:
		safe_print("Point C - Alt:",polygondict['Calt'],"Azi:",polygondict['Cazi'])
		altservo = polygondict['Calt']
		aziservo = polygondict['Cazi']
		time.sleep(1)
	else:
		safe_print("Point C - not defined")
	if 'Dalt' in polygondict:
		safe_print("Point D - Alt:",polygondict['Dalt'],"Azi:",polygondict['Dazi'])
		altservo = polygondict['Dalt']
		aziservo = polygondict['Dazi']
		time.sleep(1)
	else:
		safe_print("Point D - not defined")

def SetRandomArea(k):
	vprint("Set Random Area")
	LoadRandomArea()
	global polygondict
	if k == '1':
		polygondict.update({'Aazi': aziservo, 'Aalt': altservo})
	elif k == '2':
		polygondict.update({'Bazi': aziservo, 'Balt': altservo})
	elif k == '3':
		polygondict.update({'Cazi': aziservo, 'Calt': altservo})
	elif k == '4':
		polygondict.update({'Dazi': aziservo, 'Dalt': altservo})
	with open(polygonConfFile, 'wb') as handle:
		pickle.dump(polygondict, handle)
	vprint("Wrote polygondict:",polygondict)

def twitchXchange(lowhigh):
	vprint("Change twitch multiplier")
	global twitchX
	if lowhigh == 'lower' and twitchX > twitchMin:
		twitchX -= twitchStep
		safe_print ("Twitch multiplier decreased to",twitchX)
	elif lowhigh == 'higher' and twitchX < twitchMax:
		twitchX += twitchStep
		safe_print ("Twitch multiplier increased to",twitchX)

def get():
	global aziservo,altservo,twitch,alttwitch,azitwitch
	inkey = _Getch()
	k=inkey()
	if k=='w':
		altservo = altservo+1
	elif k=='W':
		altservo = altservo+10
	elif k=='s':
		altservo = altservo-1
	elif k=='S':
		altservo = altservo-10
	elif k=='d':
		aziservo = aziservo-1
	elif k=='D':
		aziservo = aziservo-10
	elif k=='a':
		aziservo = aziservo+1
	elif k=='A':
		aziservo = aziservo+10
	elif k=='l':
		laser("toggle")
		if laserstatus == False:
			safe_print("Laser Off")
		else:
			safe_print("Laser On")
	elif k=='c':
		altservo = altCenter
		aziservo = aziCenter
		safe_print("center")
	elif (k=='1') or (k=='2') or (k=='3') or (k=='4'):
		SetRandomArea(k)
		safe_print("Set random area",k)
	elif k=='p':
		PrintRandomArea()
	elif k=='t':
		if twitch == True:
			twitch = False
			safe_print("Twitch Off")
		else:
			alttwitch = altservo
			azitwitch = aziservo
			twitch = True
			safe_print("Twitch On")
	elif k=='-':
		twitchXchange('lower')
	elif k=='+':
		twitchXchange('higher')
	else:
		print k,helpmsg
	return k

def autolaser(*al):
	if al:
		safe_print("Random started via button touch")
	global polygondict,altservo,aziservo
	LoadRandomArea()
	if 'Aalt' not in polygondict \
	or 'Balt' not in polygondict \
	or 'Calt' not in polygondict \
	or 'Dalt' not in polygondict:
		safe_print("Random area not defined")
		return
	get_bounds_of_polygon()
	if 'polygondict' not in globals():
		safe_print("Random area not defined")
		print helpmsg
		return
	safe_print("Press CTRL-C to exit random mode.")
	AutoLaserStepCount=0
	AutoLaserStepLimit=55
	laser("on")
	try:
		while True:
			point_in_poly = get_random_point_in_polygon()
			rslptime = round(random.uniform(0.8, 2), 1)
			vprint("Random Move - Alt:",int(point_in_poly[1]),"Azi:",int(point_in_poly[0]),"Sleep:",rslptime,"Steps:",AutoLaserStepCount)
			altservo = int(point_in_poly[1])
			aziservo = int(point_in_poly[0])
			time.sleep(rslptime)
			AutoLaserStepCount = AutoLaserStepCount+1
			if AutoLaserStepCount > AutoLaserStepLimit and al:
				break
		laser("off")
		safe_print("Exiting Random Mode")

	except KeyboardInterrupt:
		safe_print("Exit Random")

safe_print("Press Q to quit.")
safe_print("Press R to enter random auto mode.")
safe_print("Press c to center.")
safe_print("Press l to toggle laser on/off.")
safe_print("Press 1, 2 ,3 or 4 to define random area.  Or p to display random area.")
safe_print("Press t to enable twitch mode.  Use - and + to change amount of twitch")
safe_print("Use a, s, d, f to move laser. Hold down Shift to move faster.")
safe_print("")

# Turn on laser
laserstatus = False
laser("toggle")

# Setup trigger for touch switch
GPIO.add_event_detect(21, GPIO.RISING, callback=autolaser, bouncetime=3000)
#GPIO.add_event_detect(21, GPIO.FALLING, callback=autolaser, bouncetime=3000)
#GPIO.add_event_detect(21, GPIO.BOTH, callback=autolaser, bouncetime=3000)

# Create threads and start them
azithread = aziThread(1, "Azi Servo Thread")
altthread = altThread(2, "Alt Servo Thread")
twitchthread = TwitchThread(3, "Servo Twiching Thread")
azithread.start()
altthread.start()
twitchthread.start()

# Center the servos to get started
altservo = altCenter
aziservo = aziCenter

try:
	while True:
		key = get()
		safe_print("Current Position - azi:",aziservo,"alt:",altservo)
		if key=='R':
			autolaser()	
		elif key=='Q':
			exitflag = True
			azithread.join
			altthread.join
			vprint("GPIO Cleanup")
			pwm.softwareReset()
			GPIO.cleanup()
			break



except KeyboardInterrupt:
	exitflag = True
	azithread.join
	altthread.join
	pwm.softwareReset()
	safe_print("Done")
	
