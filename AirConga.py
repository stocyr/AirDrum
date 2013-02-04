'''
AirConga

Copyright (C) 2013  Cyril Stoller

AirConga is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
'''

import Leap, sys
import pygame.midi


class SampleListener(Leap.Listener):
    down_sound = None
    up_sound = None
    threshold = -350
    hysteresis = 10
    down = False
    midi_out = None
    
    note = 20
    velocity = 128
    channel = 10

    def onInit(self, controller):
        print "Initialized"
        # initialize the midi device
        pygame.midi.init()
        self.set_midi_device()

    def onConnect(self, controller):
        print "Connected"

    def onDisconnect(self, controller):
        print "Disconnected"

    def onFrame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()
        hands = frame.hands()
        numHands = len(hands)

        if numHands >= 1:
            # Get the first hand
            hand = hands[0]
            
            # Check if the hand has any fingers
            fingers = hand.fingers()
            numFingers = len(fingers)
            if numFingers >= 1:
                #print '%d' % fingers[0].velocity().y
                if self.down == False and fingers[0].velocity().y < self.threshold:
                    self.midi_out.note_on(self.note, self.velocity, self.channel)
                    print 'click - timestamp: %d' % frame.timestamp()
                    self.down = True
                    
                elif self.down == True and fingers[0].velocity().y > self.hysteresis:
                    self.parent.midi_out.note_off(self.note, 0, self.channel)
                    print 'click up'
                    self.down = False
        else:
            self.down = False

    def set_midi_device():
        c = pygame.midi.get_count()
        id_device_from_settings = -1
        #print '%s midi devices found' % c
        for i in range(c):
            print '%s name: %s input: %s output: %s opened: %s' % (pygame.midi.get_device_info(i))
            if pygame.midi.get_device_info(i)[1] == 1:
                # if the device exists in the computers list, take that!
                id_device_from_settings = i
        
        print 'Default is %s' % pygame.midi.get_device_info(pygame.midi.get_default_output_id())[1]
        
        if id_device_from_settings <> -1:
            self.midi_device = id_device_from_settings
            print 'MIDI device "%s" found. Connecting.' % pygame.midi.get_device_info(id_device_from_settings)[1]
        else:
            # if it was not in the list, take the default one
            self.midi_device = pygame.midi.get_default_output_id()
            print 'Warning: No MIDI device named "%s" found. Choosing the system default ("%s").' % (1, pygame.midi.get_device_info(self.midi_device)[1])
        
        if pygame.midi.get_device_info(self.midi_device)[4] == 1:
            print 'Error: Can''t open the MIDI device - It''s already opened!'
            
        self.midi_out = pygame.midi.Output(self.midi_device)


def main():
    # Create a sample listener and assign it to a controller to receive events
    listener = SampleListener()
    controller = Leap.Controller(listener)
    
    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # The controller must be disposed of before the listener
    controller = None


if __name__ == "__main__":
    main()
