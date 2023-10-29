import httpx
from datetime import datetime
from itertools import tee, chain, islice
from operator import itemgetter

class FedocalClient:
    def __init__(self):
        self.fedocal_url = 'https://apps.fedoraproject.org/calendar/api/'

    async def get_matrix_rooms(self):
        url = f'{self.fedocal_url}locations/'
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        locations = response.json()['locations']
        matrix_rooms = [location for location in locations if 'fedoraproject.org' in location]
        return matrix_rooms

    async def get_next_meetings(self, room):
        url = f'{self.fedocal_url}meetings'
        params = {'location': f'{room}@fedoraproject.org'}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
        meetings = response.json()['meetings']

        now = datetime.utcnow()
        future_meetings = []

        for meeting in meetings:
            start_time = datetime.strptime(f"{meeting['meeting_date']} {meeting['meeting_time_start']}", "%Y-%m-%d %H:%M:%S")
            if now < start_time:
                future_meetings.append((start_time, meeting))

        return sorted(future_meetings, key=itemgetter(0))
