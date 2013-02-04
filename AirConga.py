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
    
    note = 64
    velocity = 127
    channel = 0
    
    VELOCITY_THRESHOLD = -400
    
    fingerdict = {}

    def on_init(self, controller):
        print "Initialized"
        # initialize the midi device
        pygame.midi.init()
        self.set_midi_device()

    def on_connect(self, controller):
        print "Connected"

    def on_disconnect(self, controller):
        print "Disconnected"

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()
        
        if not frame.hands.empty:
            for hand in frame.hands:
                if not hand.fingers.empty:
                    for finger in hand.fingers:
                        if finger.id in self.fingerdict:
                            # is this finger supervised already?
                            # keep track of the maximum (negative) velocity
                            self.fingerdict[finger.id]['max_velocity'] = min(finger.tip_velocity.y, self.fingerdict[finger.id]['max_velocity'])
                            # calculate acceleration a = dv/dt = (v_new-v_old)/((t_new-t_old)/1000000us/s)
                            self.fingerdict[finger.id]['acceleration'] = (finger.tip_velocity.y - self.fingerdict[finger.id]['old_velocity'])*1000000/(frame.timestamp - self.fingerdict[finger.id]['old_timestamp'])
                            # store history values (i know, it may be more elegant with frame(1), but there i have to search for the finger ID again...)
                            self.fingerdict[finger.id]['old_timestamp'] = frame.timestamp
                            self.fingerdict[finger.id]['old_velocity'] = finger.tip_velocity.y
                            
                            # check if acceleration got positive again:
                            if self.fingerdict[finger.id]['acceleration'] > 0:
                                if 'note_on' not in self.fingerdict[finger.id]:
                                    # play sound
                                    self.fingerdict[finger.id]['note_on'] = self.note
                                    velocity = -self.fingerdict[finger.id]['max_velocity'] - 400.0  # start from around zero
                                    velocity = max(0, velocity)                                     # hard limit to > 1
                                    velocity = velocity / 1500.0                                    # scale down to about 0-1
                                    velocity = min(velocity, 1.0)                                   # hard limit to 0 < velocity < 1
                                    velocity = math.pow(velocity, 1.0/2)                            # the finger weels as if it's a bit exponential -> calculate that out
                                    velocity = velocity * 126.0 + 1.0                               # scale up again to 1 - 127
                                    
                                    self.midi_out.note_on(self.note, int(velocity), self.channel)
                                    print "Note on with velocity: %.2f -> %d" % (self.fingerdict[finger.id]['max_velocity'], velocity)
                                elif finger.tip_velocity.y > self.VELOCITY_THRESHOLD:
                                    # if the note was already played and now the velocity has decreased enough, clear finger id
                                    #self.midi_out.note_on(self.note, self.velocity, self.channel)
                                    del self.fingerdict[finger.id]
                        elif finger.tip_velocity.y < self.VELOCITY_THRESHOLD:
                            self.fingerdict[finger.id] = defaultdict(dict)
                            self.fingerdict[finger.id]['old_velocity'] = finger.tip_velocity.y
                            self.fingerdict[finger.id]['old_timestamp'] = frame.timestamp
                            self.fingerdict[finger.id]['max_velocity'] = finger.tip_velocity.y
                            self.fingerdict[finger.id]['acceleration'] = 0
    
    
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

    # app closes: Remove the listener
    controller.remove_listener(listener)


if __name__ == "__main__":
    main()
