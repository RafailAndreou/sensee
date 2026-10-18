"""Guided index/thumb sampling, in palm-width units and square image coordinates."""
import math
import statistics
from gesture_engine import control


def contact_distance(hand, index, aspect):
    def xy(a, b):
        return math.hypot((a.x-b.x)*aspect, a.y-b.y)
    scale = max(xy(hand[5], hand[17]), xy(hand[0], hand[9]), 0.001)
    return xy(hand[4], hand[index])/scale, abs(hand[4].z-hand[index].z)*aspect/scale


class ContactSampler:
    def __init__(self):
        self.phase = 'idle'
        self.samples = []
        self.contact = None
        self.result = None
        self.epoch = -1

    def start(self, phase):
        if phase not in ('contact', 'open', 'cancel'):
            raise ValueError('Phase must be contact, open or cancel')
        with control.lock:
            if phase == 'open' and self.contact is None:
                raise ValueError('Sample contact first')
            self.phase, self.samples, self.result = phase, [], None
            self.epoch = control.epoch
            if phase == 'contact':
                self.contact = None

    def observe(self, hand, aspect):
        with control.lock:
            if self.phase not in ('contact', 'open') or self.epoch != control.epoch:
                return
            self.samples.append(contact_distance(hand, 8, aspect))
            if len(self.samples) < 30:
                return
            xy = statistics.median(x[0] for x in self.samples)
            depth = statistics.median(x[1] for x in self.samples)
            if self.phase == 'contact':
                self.contact = (xy, depth)
                self.phase = 'contact_ready'
            elif xy <= self.contact[0]*1.5:
                self.phase = 'retry_open'
            else:
                self.result = {'enabled': True, 'contactRatio': min(1, max(.02, (xy+self.contact[0])/2)),
                               'depthRatio': min(1, max(.01, self.contact[1]*1.5+.02))}
                self.phase = 'ready'

    def status(self):
        with control.lock:
            if self.phase in ('contact', 'open') and self.epoch != control.epoch:
                self.phase, self.samples = 'interrupted', []
            return {'phase': self.phase, 'samples': len(self.samples), 'required': 30, 'result': self.result}


sampler = ContactSampler()
