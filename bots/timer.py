#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime as dt
class Timer():
    def __init__(self):
        self.start_time = dt.now()

    def duration(self):
        return (dt.now() - self.start_time).total_seconds()