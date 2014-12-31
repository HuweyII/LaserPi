LaserPi
https://github.com/HuweyII/LaserPi
v. 1.0

Video of version 0.1 (very old) of this is available on youtube
http://youtu.be/nJSfPyN7-30

Files:
README.md -- This file
LaserPi-Main.py -- Main program file (execute this one)
Adafruit_I2C.py -- I2C library courtesy of Adafruit
Adafruit_PWM_Servo_Driver.py -- PWM Server Driver library courtesy of Adafruit
HARDWARE.txt -- Instructions for building the hardware
INSTALL.txt -- Instructions for software install


General description:
This project is for building a RaspberyPi that will drive your cats nuts.  It is essentially a Pi that controls two servos with a laser attached.  Through clever coding the software on the Pi will drive the laser dot around the room in a way that the cat should enjoy.  It also includes a touch switch so that the cat (or can opener (a.k.a. Human)) can start a laser sequence with a light touch of the nose (or finger).


The Pi drives the two servos via a PWM servo controller; One servo for Azimuth movement (left right) and one for Altitude movement (up down).   
	NOTE:It is possible to drive the servos directly from the Pi via software via software PWM but this will cause overheating of the servos and may even cause them to strip their gears.
        NOTE:You can use any cheap micro or mini servos.  However good quality digital servos will give better control.  A tiny amount of slop in the gears of cheap servos multiplies to a having the laser not move when you want it to.  Especially the Twitch function in the software won't really work with cheap servos because it moves the servos tiny amounts to keep the cat interested.


Attached to these servos is a low power laser powered directly from one of the GPIO output on the Pi.  For this reason it is important to use a very low power laser.  The one linked below draws ~20mA, which is well within what the RaspberryPi 5v rail has to spare.  This is slightly above the recommended 16mA maximum draw on a GPIO, but seems to work fine in this configuration.


The whole unit is powered from a single 5v source for convenience.  However this source needs to be high quality.  The power supply linked in HARDWEAR.txt has proven to be a stable source for this project.  
        NOTE:It is possible to power this whole setup via the USB connector on the Pi.  Current should never exceed the onboard fuse rating. However this proved problematic in testing and isn't recommended.  In testing many cheap USB power supplies weren't stable enough when the servos where moving and the Pi would reboot.  For instance an Apple iPad  power supply seemed to do the job pretty well, but a no-name brand USB power supply with the same ratings caused constant reboots.


Usage:
Control the laser manually.  You can just point the laser where you want it with the traditional gaming movement keys.  a, s, d, f, hold shift to make it move faster.

Turn the laser on and off with the l key.

Make the laser constantly twitch by hitting the t key.  Twitch amount can be adjusted with the - and + keys.  NOTE: Twitching stops automatically when the laser is switched off.

Make the laser point to a random point within a defined space.  To start this mode press R (capital R, so shift+r), to exit random mode you must use CTRL-c.  Random won't function until you set points to define the random area.  

To set the random defined space drive the laser to a corner of space with the a, s, d, f keys then press 1 to define the first point.  Then move the laser to the next corner and define it by pressing 2.   Move the laser to the third and fourth points and define them by pressing the  3 and 4 keys, respectively.  The software needs 4 points, and they need to be in some order.  Imagine a line connecting point 1 to 2, 2 to 3, 3 to 4 and 4 to 1.  However they don't need to be in any particular shape.  Any four sided shape is fine.

Display the random points defined by pressing the p key.  The laser will drive to each point in turn, showing your area.

To quit use capital Q

Theory Of Operation:
The main program just sets up variables and then listens for key strokes, changing variables as need.  Most of the real work is done by various threads which the main program starts.

The servos are controlled by one thread each.  Any function which would move a servo must change a variable that this thread will notice changed, wake up, move the servo, and then go back to sleep. Running things in this way prevents arguments by various functions over who should be moving servos.

THREADS:
aziThread - Runs moveazi function 
Commands the Azi servo.  The only way the Azi servo is ever moved is via this thread.

altThread - Runs movealt function.
Commands the Alt servo.  The only way the Alt servo is ever moved is via this thread.

TwitchThread - Runs twitchy function.
 When twitch is active this thread randomly changes the aziservo and altservo variables random amounts (thus causing other threads to move the servos).  Then waits a short time and does it again.  Also after 10 random steps it sets the variables back to where they were so that there isn’t much wandering around.
    twitchy function is aware of changes made to the altservo and aziservo variables made by other threads.   In such a way that twitching continues but servos stay in the area commanded by other threads.
    twitchy function isn’t aware of servo limits.  However the threads that move the servos are and won’t move the servos past their limits.

An additional thread started as a trigger thread by the adafruit code for the touch switch (GPIO.add_event_detect)  This acts as an interrupt driven switch so that we don’t have to waste a bunch of CPU checking the touch switch all the time.

RANDOM (autolaser function):
Random works by feeding four points of a polygon (as X,Y coordinates) into the Polygon function of the shapely.geometry python module.  Getting from that the bounds of the Polygon.  This happens in the get_bounds_of_polygon function.

Random then goes into a loop where it runs the get_random_point_in_polygon function.  In which a random coordinate (X,Y) is generated within the servo’s range of motion.  The Point function of the shapely.geometry python module is then queried to find out if the randomly generated point is within the previously defined polygon.  If not a loop tried again.  If the randomly generated point is within the polygon the altservo and aziservo variables are changed and the servo’s drive to the new point.  autolaser then waits a random amount of time before starting again.

If started from the touch switch random will stop it’s loop after AutoLaserStepCount number of steps.  If started by the R key it will run forever until the loop is broken with CTRL-c

Polygon points are read and stored in a file via the pickle.dump python module.  This way when the program stops and starts again later it still knows the points of it’s polygon.
