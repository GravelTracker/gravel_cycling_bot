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
            gcb.send_status('offline')
            break
        except Exception:
            gcb.send_status('error')
            traceback.print_exc()
            break
