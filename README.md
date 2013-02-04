ConsoleMotionRecorder
=====================

Air drum with a Leap device

## Platforms

This should work under Windows, Linux and Mac, though only Windows was tested yet.

## Requirements

This tool requires a python 2.x installation and a Leap Motion device (www.leapmotion.com) with installed Leap app v0.7.3 or higher.
Alongside with the source file *ConsoleMotionRecorder.py*, the Leap python API (again SDK v0.7.3 or higher) should be provided in the same directory:

* *Leap.py*
* *_LeapPython.pyd*
* *Leap.dll*

## Usage

Start the tool, connect the Leap and make sure the Leap app is running. Moving down a finger fast enough will trigger the MIDI note E4 on MIDI channel 0 with velocity depending on the speed of the finger.