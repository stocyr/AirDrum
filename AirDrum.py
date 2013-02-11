'''
AirDrum

Copyright (C) 2013  Cyril Stoller

AirDrum is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
'''

import Leap, sys, math
from collections import defaultdict
import pygame.midi


def mid_position(VectorA, VectorB):
    return VectorA + (VectorB - VectorA) / 2

class DrumListener(Leap.Listener):
    midi_out = None
    play_midi = None
    note_kick = 36 # sometimes: 48
    note_snare = 40 # sometimes: 52
    midi_channel = 0
    
    VELOCITY_THRESHOLD = -600 # m/s
    NOTE_HOLD = 40000 # microseconds
    MULTISAMPLE_THRESHOLD = 0.5
    
    fingerdict = {}
    notes_playing = []
    sounds = {}

    def on_init(self, controller):
        print "Initialized\n"

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()
        
        # search trough all the pointables:
        if not frame.pointables.empty and self.play_midi != None:
            for pointable in frame.pointables:
                # does anyone excess the velocity threshold and isn't on the list already? (WARNING: since velocity is negative, < is used!)
                if pointable.tip_velocity.y < self.VELOCITY_THRESHOLD and pointable.id not in self.fingerdict:
                    # add it to supervisor list.
                    self.fingerdict[pointable.id] = defaultdict(dict)
                    # store the actual position to determine the hit position on the XZ-plane
                    self.fingerdict[pointable.id]['PosA'] = pointable.tip_position
            
        # process the existing IDs in list
        del_array = []
        for hit_id in self.fingerdict:
            hit = self.fingerdict[hit_id]
            # already played?
            if 'note' in hit:
                # hold the note for a certain time, then kill it
                if frame.timestamp - hit['timestamp'] > self.NOTE_HOLD:
                    # DEBUG:
                    print "\t%s off " % ("snare" if hit['note'] == self.note_snare else "kick")
                    
                    if self.play_midi:
                        self.midi_out.note_off(hit['note'], 0, self.midi_channel)
                    self.notes_playing.remove(hit['note'])
                    del_array.append(hit_id)
            # not played yet:
            else:
                pointable = frame.pointable(hit_id)
                pointable_old = controller.frame(1).pointable(hit_id)
                # finger ID even visible yet?
                if pointable.is_valid:
                    # detect whether the hit should play already: has the negative velocity decreased? (WARNING: since velocity is negative, > is used!)
                    if pointable_old.is_valid and pointable.tip_velocity.y > pointable_old.tip_velocity.y:
                        # determine the volume of the note: since the pointable has reached its lowermost point, the last point was the lowest one.
                        hit['velocity'] = pointable_old.tip_velocity.y
                        # determine which note to play: if it's on the right, play kick
                        if pointable.tip_position.x > 0:
                            hit['note'] = self.note_kick
                        else:
                            hit['note'] = self.note_snare
                        
                        # check if the note may be playing yet
                        if hit['note'] in self.notes_playing:
                            # if already playing: delete hit!
                            del_array.append(hit_id)
                        else:
                            # store the position to determine the hit position on the XZ-plane
                            hit['PosB'] = pointable.tip_position
                            hit['Pos'] = mid_position(hit['PosA'], hit['PosB'])
                            # play the actual sound
                            self.play_sound(pointable, hit)
                # finger not visible anymore
                else:
                    # then just delete it.
                    del_array.append(hit_id)
            
        # delete dead dictionary items
        for hit_id in del_array:
            del self.fingerdict[hit_id]
        
    
    def play_sound(self, pointable, hit):
        # safe timestamp
        hit['timestamp'] = pointable.frame.timestamp
        
        # calculate velocity
        velocity = - hit['velocity'] - 500.0        # start from around zero
        if pointable.is_tool:
            velocity /= 6000.0                      # if it's a tool, greater velocities can be achieved -> scale it more
        else:
            velocity /= 4000.0                      # if it's a finger, don't scale it as much as a tool
        velocity = min(velocity, 1.0)               # hard limit to 0 < velocity < 1
        velocity = max(0.0, velocity)
        velocity = math.pow(velocity, 0.4)          # it feels as if it's a bit exponential -> calculate that out
        
        # play the actual hit
        if self.play_midi:
            velocity = velocity * 126.0 + 1.0           # scale up again to 1 - 127
            # play note on midi out
            # DEBUG:
            print "\t%s on with velocity: %.2f m/s -> Midi %d" % (("snare" if hit['note'] == self.note_snare else "kick"), hit['velocity'], velocity)
            self.midi_out.note_on(hit['note'], int(velocity), self.midi_channel)
        else:
            # play audio sound
            # determine which multisample (2 times multisamples each)
            if velocity < self.MULTISAMPLE_THRESHOLD:
                # soft sample
                multisample = 0
                #velocity /= self.MULTISAMPLE_THRESHOLD
            else:
                # hard sample
                multisample = 1
                velocity -= self.MULTISAMPLE_THRESHOLD/3
                velocity /= (1-self.MULTISAMPLE_THRESHOLD/3)
            # DEBUG:
            print "\t%s (%s) on with velocity: %.2f m/s -> Volume %.2f" % (("snare" if hit['note'] == self.note_snare else "kick"), ("hard" if multisample else "soft"), hit['velocity'], velocity)
            self.sounds[hit['note']][multisample].set_volume(velocity)
            self.sounds[hit['note']][multisample].play()
        
        # register note in array:
        self.notes_playing.append(hit['note'])


    def init_midi(self):
        self.play_midi = True
        # initialize the midi device
        pygame.midi.init()
        
        # list all Midi output devices
        print ""
        c = pygame.midi.get_count()
        default = pygame.midi.get_default_output_id()
        for i in range(c):
            if pygame.midi.get_device_info(i)[3] == 1:
                #print '%s name: %s input: %d output: %d opened: %d' % (pygame.midi.get_device_info(i))
                print '%d: "%s"%s' % (i, pygame.midi.get_device_info(i)[1], " (default)" if i == default else "")
        
        # let user choose one
        choice = raw_input("Choose a Midi output (press enter for default): ")
        choice = int(choice) if choice.isdigit() else -1
        if choice in range(c) and pygame.midi.get_device_info(choice)[3] == 1:
            # valid?
            print 'Connecting to "%s".\n' % pygame.midi.get_device_info(choice)[1]
        else:
            # invalid? (if it was not in the list, not an output or just [enter]) take the default one
            choice = pygame.midi.get_default_output_id()
            print 'Connecting to the system default ("%s").\n' % pygame.midi.get_device_info(default)[1]
        
        # if it's the Microsoft GS Wavetable Synth, choose Midi channel 10 to play drums
        if pygame.midi.get_device_info(choice)[1] == "Microsoft GS Wavetable Synth":
            print "Since the Microsoft GS Wavetable Synth was selected, Midi channel has switched to 10"
            self.midi_channel = 9
        
        # try to open the device
        if pygame.midi.get_device_info(choice)[4] == 1:
            print "Error: Can't open the MIDI device - It's already opened!"
        else:
            self.midi_out = pygame.midi.Output(choice)

    def init_audio(self):
        self.play_midi = False
        
        print "\nSetting up audio files.\n"
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.init()
        self.sounds[self.note_snare] = (pygame.mixer.Sound('Snare_soft.ogg'), pygame.mixer.Sound('Snare_hard.ogg'))
        self.sounds[self.note_kick] = (pygame.mixer.Sound('Kick_soft.ogg'), pygame.mixer.Sound('Kick_hard.ogg'))

def main():
    # Create a listener and controller
    listener = DrumListener()
    controller = Leap.Controller()
    
    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    
    # let user choose betweed playing audio sound or Midi notes
    print "0: Audio (default)"
    print "1: Midi"
    choice = raw_input("Choose between Audio or Midi output: (press enter for default): ")
    choice = int(choice) if choice.isdigit() else -1
    
    choice
    
    if choice == 1:
        listener.init_midi()
    else:
        listener.init_audio()
    
    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()
    
    print "Exiting..."
    
    # close MIDI socket
    #listener.midi_out.close()
    #pygame.midi.quit()

    # App closes: Remove the listener
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
