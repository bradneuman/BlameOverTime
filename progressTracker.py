# Copyright (c) 2014 Brad Neuman

import time
import datetime
import math

class ProgressTracker:
    """
    This is a class to print a progress percentage and a rough ETA. It doesn't do a very good job, but its
    very easy to add to something and get some kind of half-assed idea of when things will finish, assuming
    all of those "things" take the same amount of time. Timer starts on first update, so put the update at the
    top of the loop

    """

    def __init__(self, num_items):
        self.num_items = num_items

        self.start_time = None

        # config

        # don't show anything until this much time has passed
        self.time_delay = 1.75

        # output
        self.index = -1
        self.timePer = None
        self.lastPrint = None

        itemStrWidth = math.ceil(math.log(num_items+1, 10))

        self.format_str = '# %%%dd / %%%dd (%%5.2f%%%%) ETA: %%s' % (itemStrWidth, itemStrWidth)
        
        
    def Update(self, itemInput = None):
        "tell the progress tracker that we are on the given number out of the previously specified number"
        "if the argument isn't provided, it is assumed to be incremented by 1"

        if itemInput == None:
            item = self.index + 1
        else:
            item = itemInput

        self.index = item

        if self.start_time == None or item == 0:
            self.start_time = time.time()
            return ''

        elapsed = time.time() - self.start_time
        self.timePer = elapsed / float(item)

        return str(self)

    def Done(self):
        "return a string to print about how long things took"

        if self.start_time == None:
            return ''

        elapsed = time.time() - self.start_time

        if elapsed > self.time_delay:
            return "Completed in %s" % str(datetime.timedelta(seconds = elapsed))
        else:
            return ''

    def ShouldPrint(self):
        "return true if printing something now seems like a good idea. This doens't work if you print the results"
        "of the Update() call"

        if self.start_time == None:
            return False

        if self.lastPrint == None:
            return True

        elapsed = time.time() - self.lastPrint

        return elapsed > self.time_delay

    def __str__(self):
        if not self.timePer:
            return ''

        if self.timePer * self.index < self.time_delay:
            return ''

        timeLeft = self.timePer * (self.num_items - self.index)
        if timeLeft > 0.0:
            self.lastPrint = time.time()
            return self.format_str % (self.index, self.num_items, 100.0 * self.index / self.num_items,
                                      str(datetime.timedelta(seconds = timeLeft)))
        else:
            return ''



