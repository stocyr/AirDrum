AirDrum
=======

Air drum with the Leap device

## Platforms

This should work under Windows, Linux and Mac, though only Windows was tested yet.

## Requirements

This tool requires a python 2.x installation and a Leap Motion device (www.leapmotion.com) with installed Leap app v0.7.3 or higher.
Alongside with the source file *AirDrum.py*, the Leap python API (again SDK v0.7.3 or higher) should be provided in the same directory:

* *Leap.py*
* *_LeapPython.pyd*
* *Leap.dll*

If no Midi output is used, there have to be four audio files in the same directory as well:

* *Kick_soft.ogg*
* *Kick_hard.ogg*
* *Snare_soft.ogg*
* *Snare_hard.ogg*

If the Midi output want to be used instead, there has at least one Midi output device to be present.

## Usage

Start the tool, connect the Leap and make sure the Leap app is running. Moving down a finger/hand/tool fast enough will trigger a drum. If you hit on the left side of the Leap, a snare drum will be triggered. On the right side, a kick drum will be triggered. The volume is depending on the speed of the finger/hand/tool.

### Midi

If you selected to use a Midi output, the kick drum hit will be sent on note 36 (C1) and the snare drum hit on note 40 (E1).
Note that if you require as little latency as possible during playing, you should absolutely select the Midi output instead of the audio output. 

### Audio

If you selected to use an audio output, there are two double sampled drum samples for each snare and kick drum. The *hard* sample will only play above a certain finger/hand/tool speed of the hit.
If you notice sound playback failures, try setting the sample rate of the audio device initialization to a higher value (the last parameter of the function `pygame.mixer.pre_init()` in `DrumListener::init_audio()`)