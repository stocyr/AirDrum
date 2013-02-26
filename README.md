AirDrum
=======

Air drum with the Leap device

Video: http://www.youtube.com/watch?v=xdm_2FO44ug

## Platforms

This should work under Windows, Linux and Mac, though only Windows was tested yet.

## Requirements

Python 2.x (32-bit):
* *http://python.org/ftp/python/2.7.3/python-2.7.3.msi*

PyGame (32-bit):
* *http://pygame.org/ftp/pygame-1.9.1.win32-py2.7.msi*

Leap Motion device and Leap app v0.7.3 or higher.
* *http://www.leapmotion.com/*

Alongside with the source file *AirDrum.py*, the Leap python API (again SDK v0.7.3 or higher) should be provided in the same directory:
A copy of the following three files are available when you checkout, AirDrum.
* *Leap.py*
* *_LeapPython.pyd (no underscore( _ ) from v0.7.4 onwards)*
* *Leap.dll*

It is preferred to replace these three files from your local LeapSDK installation folder.

* *\Leap_Developer_Kit_\<v0.7.3 or higher\>_\<OS\>\Leap_SDK\lib\Leap.py*
* *\Leap_Developer_Kit_\<v0.7.3 or higher\>_\<OS\>\Leap_SDK\lib\x86\Leap.dll*
* *\Leap_Developer_Kit_\<v0.7.3 and lower\>_\<OS\>\Leap_SDK\lib\x86\\_LeapPython.pyd*
* *OR*
* *\Leap_Developer_Kit_\<v0.7.4 or higher\>_\<OS\>\Leap_SDK\lib\x86\\LeapPython.pyd*


If no Midi output is used, there have to be four audio files in the same directory as well:

* *Kick_soft.ogg*
* *Kick_hard.ogg*
* *Snare_soft.ogg*
* *Snare_hard.ogg*

If the Midi output want to be used instead, there has at least one Midi output device to be present.

## Usage

Start the tool, connect the Leap and make sure the Leap app is running. Moving down a finger/hand/tool fast enough will trigger a drum. If you hit on the left side of the Leap, a snare drum will be triggered. On the right side, a kick drum will be triggered. The volume is depending on the speed of the finger/hand/tool.

* *python AirDrum.py*
* *...*
* *...*

"Press Enter to quit...", after you see this printed on the console, you can start drumming...

* *Happy Drumming... /\ || \\\ // || /\ /\*


### Midi

If you selected to use a Midi output, the kick drum hit will be sent on note 36 (C1) and the snare drum hit on note 40 (E1).
Note that if you require as little latency as possible during playing, you should absolutely select the Midi output instead of the audio output. 

### Audio

If you selected to use an audio output, there are two double sampled drum samples for each snare and kick drum. The *hard* sample will only play above a certain finger/hand/tool speed of the hit.
If you notice sound playback failures, try setting the sample rate of the audio device initialization to a higher value (the last parameter of the function `pygame.mixer.pre_init()` in `DrumListener::init_audio()`)



### Dev Tip:
For better performance and clean console:
Search for 'DEBUG' in the AirDrum.py and comment out any 'print' lines. Comment char is '#'.
