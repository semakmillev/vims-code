import asyncio
from asyncio import sleep
from concurrent.futures.thread import ThreadPoolExecutor

from vims_code.models.tick_step import TickStep
from vims_code.game.levels import Level, check_level_finish
from vims_code.game.scores import Result
from vims_code.game.team import Team
from vims_code.ticks.api import Tick

t = ThreadPoolExecutor()



