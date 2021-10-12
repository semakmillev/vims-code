import datetime

from vims_code.models.team_timer_event_list import TimerEvents


class TeamTimer(object):
    def __init__(self, timer_id, level_id):
        self.timer_id = timer_id
        self.level_id = level_id
        # self.num_of_steps = 0
        self.timer_events = []

    def add_event(self, event, event_date):
        event_date = event_date.split('.')[0]
        event_date = datetime.datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%S')
        self.timer_events.append({'event': event, 'event_date': event_date})

    def get_num_of_steps(self, current_date: datetime.datetime):
        num_of_steps = 0
        start_date: datetime.datetime = None
        for timer_event in self.timer_events:
            if timer_event['event'] == TimerEvents.STARTED:
                start_date: datetime.datetime = timer_event['event_date']
            if timer_event['event'] in (TimerEvents.PAUSED, TimerEvents.FINISHED, TimerEvents.FAILED):

                num_of_steps += (timer_event['event_date'] - start_date).seconds
                start_date = None
        if start_date:
            num_of_steps += (current_date - start_date).seconds
        return num_of_steps
