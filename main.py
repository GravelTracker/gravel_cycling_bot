#!/usr/bin/env python

import traceback
from env import EnvVarSetter
from bots.bot import GravelCyclingBot

gcb = GravelCyclingBot()

if __name__ == '__main__':
  while True:
    try:
      gcb.run()
    except KeyboardInterrupt:
      break
    except Exception:
      traceback.print_exc()
      break