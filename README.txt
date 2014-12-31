LaserPi
https://github.com/HuweyII/LaserPi
v. 1.0
fixing formating

Files:
README.md -- This file
LaserPi-Main.py -- Main program file (execute this one)
Adafruit_I2C.py -- I2C library curtosy of Adafruit
Adafruit_PWM_Servo_Driver.py -- PWM Server Driver library curtosy of Adafruit
HARDWARE.txt -- Instructions for building the hardware
INSTALL.txt -- Instructions for software install


General description:
This project is for building a RaspberyPi that will drive your cats nuts.  It’s essentially a Pi that controls two servos with a laser attached.  Through clever coding the software on the Pi will drive the laser dot around the room in a way that the cat should enjoy.  It also includes a touch switch so that the cat (or can opener (a.k.a. Human)) can start a laser sequence with a light touch of the nose (or finger).


The Pi drives the two servos via a PWM servo controller.; One servo for Azimuth movement (left right) and one for Altitude movement (up down).   
NOTE:It is possible to drive the servos directly from the Pi via software via software PWM but this will cause overheating of the servos and may even cause them to strip their gears.
        NOTE:You can use any cheap micro or mini servos.  However good quality digital servos will give better control.  A tiny amount of slop in the gears of cheap servos multiplies to a having the laser not move when you want it to.  Especially the “Twitch” function in the software won’t really work with cheap servos because it moves the servos tiny amounts to keep the cat interested.


Attached to these servos is a low power laser powered directly from one of the GPIO output on the Pi.  For this reason it’s important to use a very low power laser.  The one linked below draws ~20mA, which is well within what the RaspberryPi’s 5v rail has to spare.  This is slightly above the recommended 16mA maximum draw on a GPIO, but seems to work fine in this configuration.


The whole unit is powered from a single 5v source for convenience.  However this source needs to be high quality.  The power supply linked below has proven to be a stable source for this project.  
        NOTE:It is possible to power this whole setup via the USB connector on the Pi.  Current should never exceed the onboard fuse rating. However this proved problematic in testing and isn’t recommended.  Many cheap USB power supplies weren’t stable enough when the servos where moving and the Pi would reboot.  For instance an Apple iPad  power supply seemed to do the job pretty well, but a no-name brand USB power supply with the same ratings caused constant reboots.


Usage:
Control the laser manually.  You can just point the laser where you want it with the traditional gaming movement keys.  a, s, d, f, hold shift to make it move faster.


Turn the laser on and off with the l key.


Make the laser constantly twitch by hitting the t key.  Twitch amount can be adjusted with the - and + keys.  NOTE: Twitching stops automatically when the laser is switched off.


Make the laser point to a random point within a defined space.  To start this mode press R (capital R, so shift+r), to exit random mode you must use CTRL-c.  Random won’t function until you set points to define the random area.  


To set the random defined space drive the laser to a corner of space with the a, s, d, f keys then press 1 to define the first point.  Then move the laser to the next corner and define it by pressing 2.   Move the laser to the third and fourth points and define them by pressing the  3 and 4 keys, respectively.  The software needs 4 points, and they need to be in some order.  Imagine a line connecting point 1 to 2, 2 to 3, 3 to 4 and 4 to 1.  However they don’t need to be in any particular shape.  Any four sided shape is fine.


Display the random points defined by pressing the p key.  The laser will drive to each point in turn, showing your area.


To quit use capital Q
