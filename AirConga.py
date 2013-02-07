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
    down_sound = None
    up_sound = None
    midi_out = None
    
    note_snare = 52
    note_kick = 48
    velocity = 127
    channel = 0
    
    VELOCITY_THRESHOLD = -500
    
    fingerdict = {}
    
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
        
        if not frame.pointables.empty:
            # DEBUG:
            self.file.write("%f\t%d" % ((frame.timestamp - controller.frame(1).timestamp)/1000000.0, frame.id))
                             
            for pointable in frame.pointables:
                if pointable.id in self.fingerdict:
                    # is this finger supervised already?
                    # keep track of the maximum (negative) velocity
                    self.fingerdict[pointable.id]['max_velocity'] = min(pointable.tip_velocity.y, self.fingerdict[pointable.id]['max_velocity'])
                    # calculate acceleration a = dv/dt = (v_new-v_old)/((t_new-t_old)/1000000us/s)
                    self.fingerdict[pointable.id]['acceleration'] = (pointable.tip_velocity.y - self.fingerdict[pointable.id]['old_velocity'])*1000000/(frame.timestamp - self.fingerdict[pointable.id]['old_timestamp'])
                    
                    
                    if 'note_on' not in self.fingerdict[pointable.id]:
                        # check if acceleration got positive again:
                        if self.fingerdict[pointable.id]['acceleration'] > 0:
                            # play sound according to position
                            if pointable.tip_position.x > 0:
                                # if it's on the right, play kick
                                self.fingerdict[pointable.id]['note_on'] = self.note_kick
                                # DEBUG:
                                self.file.write("\tKick on")
                            else:
                                self.fingerdict[pointable.id]['note_on'] = self.note_snare
                                # DEBUG:
                                self.file.write("\tSnare on")
                            velocity = -self.fingerdict[pointable.id]['max_velocity'] - 400.0   # start from around zero
                            velocity = max(0, velocity)                                         # hard limit to > 1
                            if pointable.is_tool:                                               # scale down to about 0-1
                                velocity = velocity / 6000.0                                    # if it's a tool, greater velocities can be achieved -> scale it more
                            else:
                                velocity = velocity / 4000.0                                    # if it's a finger, don't scale it as much as a tool
                            velocity = min(velocity, 1.0)                                       # hard limit to 0 < velocity < 1
                            velocity = math.pow(velocity, 0.4)                                  # it feels as if it's a bit exponential -> calculate that out
                            velocity = velocity * 126.0 + 1.0                                   # scale up again to 1 - 127
                            
                            self.midi_out.note_on(self.fingerdict[pointable.id]['note_on'], int(velocity), self.channel)
                            print "%d\t%s on with velocity: %.2f -> %d" % (frame.timestamp, ("snare" if self.fingerdict[pointable.id]['note_on'] == self.note_snare else "kick"), self.fingerdict[pointable.id]['max_velocity'], velocity)
                        
                        # store history values (i know, it may be more elegant with frame(1), but there i have to search for the finger ID again...)
                        self.fingerdict[pointable.id]['old_timestamp'] = frame.timestamp
                        self.fingerdict[pointable.id]['old_velocity'] = pointable.tip_velocity.y
                    elif pointable.tip_velocity.y > self.VELOCITY_THRESHOLD:
                        # if the note was already played and now the velocity has decreased enough, clear finger id
                        self.midi_out.note_off(self.fingerdict[pointable.id]['note_on'], 0, self.channel)
                        print "%d\t%s off " % (frame.timestamp, ("snare" if self.fingerdict[pointable.id]['note_on'] == self.note_snare else "kick"))
                        del self.fingerdict[pointable.id]
                        # DEBUG:
                        self.file.write("\toff")
                elif pointable.tip_velocity.y < self.VELOCITY_THRESHOLD:
                    self.fingerdict[pointable.id] = defaultdict(dict)
                    self.fingerdict[pointable.id]['old_velocity'] = pointable.tip_velocity.y
                    self.fingerdict[pointable.id]['old_timestamp'] = frame.timestamp
                    self.fingerdict[pointable.id]['max_velocity'] = pointable.tip_velocity.y
                    self.fingerdict[pointable.id]['acceleration'] = 0
            
            # DEBUG:
            self.file.write("\t%s\n" % self.fingerdict)
            

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
            self.midi_device = id_device_from_settings
            print 'MIDI device "%s" found. Connecting.' % pygame.midi.get_device_info(id_device_from_settings)[1]
        else:
            # if it was not in the list, take the default one
            self.midi_device = pygame.midi.get_default_output_id()
            print 'Warning: No MIDI device named "%s" found. Choosing the system default ("%s").' % ("Fast Track Pro MIDI Out", pygame.midi.get_device_info(self.midi_device)[1])
        
        if pygame.midi.get_device_info(self.midi_device)[4] == 1:
            print 'Error: Can''t open the MIDI device - It''s already opened!'
            
        self.midi_out = pygame.midi.Output(self.midi_device)


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

    # app closes: Remove the listener
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
