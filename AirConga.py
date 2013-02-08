'''
AirConga

Copyright (C) 2013  Cyril Stoller

AirConga is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
'''

import Leap, sys, math
from collections import defaultdict
import pygame.midi

class CongaListener(Leap.Listener):
    midi_out = None
    
    note_snare = 52
    note_kick = 48
    channel = 0
    
    VELOCITY_THRESHOLD = -600
    NOTE_HOLD = 40000 # microseconds
    
    fingerdict = {}
    notes_playing = []
    
    # DEBUG:
    file = None

    def on_init(self, controller):
        print "Initialized"
        # initialize the midi device
        pygame.midi.init()
        self.set_midi_device()

    def on_connect(self, controller):
        print "Connected"
        
        # DEBUG:
        self.file = open("dict_output.txt", 'w')

    def on_disconnect(self, controller):
        print "Disconnected"

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()
        
        # search trough all the pointables:
        if not frame.pointables.empty:
            # DEBUG:
            self.file.write("%f\t%d" % ((frame.timestamp - controller.frame(1).timestamp)/1000000.0, frame.id))
            for pointable in frame.pointables:
                # does anyone excess the velocity threshold and isn't on the list already? (WARNING: since velocity is negative, < is used!)
                if pointable.tip_velocity.y < self.VELOCITY_THRESHOLD and pointable.id not in self.fingerdict:
                    # add it to supervisor list.
                    self.fingerdict[pointable.id] = defaultdict(dict)
            
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
                    self.midi_out.note_off(hit['note'], 0, self.channel)
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
                            self.play_sound(pointable, hit)
                # finger not visible anymore
                else:
                    # then just delete it.
                    del_array.append(hit_id)
            
        # delete dead dictionary items
        for hit_id in del_array:
            del self.fingerdict[hit_id]
        
        # DEBUG:
        if not frame.pointables.empty: self.file.write("\t%s\n" % self.fingerdict)
        
    
    def play_sound(self, pointable, hit):
        # safe timestamp
        hit['timestamp'] = pointable.frame.timestamp
        
        # DEBUG:
        self.file.write("\tKick on" if hit['note'] == self.note_kick else "\tSnare on")
        
        # calculate velocity
        velocity = - hit['velocity'] - 500.0     # start from around zero
        if pointable.is_tool:
            velocity = velocity / 6000.0            # if it's a tool, greater velocities can be achieved -> scale it more
        else:
            velocity = velocity / 4000.0            # if it's a finger, don't scale it as much as a tool
        velocity = min(velocity, 1.0)               # hard limit to 0 < velocity < 1
        velocity = max(0.0, velocity)
        velocity = math.pow(velocity, 0.4)          # it feels as if it's a bit exponential -> calculate that out
        velocity = velocity * 126.0 + 1.0           # scale up again to 1 - 127
        
        # play note on midi out
        self.midi_out.note_on(hit['note'], int(velocity), self.channel)
        # DEBUG:
        print "\t%s on with velocity: %.2f -> %d" % (("snare" if hit['note'] == self.note_snare else "kick"), hit['velocity'], velocity)
        
        # register note in array:
        self.notes_playing.append(hit['note'])

    def set_midi_device(self):
        c = pygame.midi.get_count()
        id_device_from_settings = -1
        #print '%s midi devices found' % c
        for i in range(c):
            print '%s name: %s input: %s output: %s opened: %s' % (pygame.midi.get_device_info(i))
            if pygame.midi.get_device_info(i)[1] == "Fast Track Pro MIDI Out":
                # if the device exists in the computers list, take that!
                id_device_from_settings = i
        
        print 'Default is %s' % pygame.midi.get_device_info(pygame.midi.get_default_output_id())[1]
        
        if id_device_from_settings <> -1:
            midi_device_id = id_device_from_settings
            print 'MIDI device "%s" found. Connecting.' % pygame.midi.get_device_info(id_device_from_settings)[1]
        else:
            # if it was not in the list, take the default one
            midi_device_id = pygame.midi.get_default_output_id()
            print 'Warning: No MIDI device named "%s" found. Choosing the system default ("%s").' % ("Fast Track Pro MIDI Out", pygame.midi.get_device_info(self.midi_device)[1])
        
        if pygame.midi.get_device_info(midi_device_id)[4] == 1:
            print 'Error: Can''t open the MIDI device - It''s already opened!'
            
        self.midi_out = pygame.midi.Output(midi_device_id)


def main():
    # Create a listener and controller
    listener = CongaListener()
    controller = Leap.Controller()
    
    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    
    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()
    print "Exiting..."
    
    # DEBUG:
    listener.file.close()
    
    # close MIDI socket
    listener.midi_out.close()
    pygame.midi.quit()

    # app closes: Remove the listener
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
