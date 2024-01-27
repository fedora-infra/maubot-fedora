from datetime import datetime
from itertools import islice
from operator import itemgetter

import arrow
import httpx

from ..constants import NL


class FedocalClient:
    def __init__(self):
        self.fedocal_url = "https://apps.fedoraproject.org/calendar/api/"

    async def _get(self, endpoint, **kwargs):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.fedocal_url + endpoint, **kwargs)
        return response

    def _check_errors(self, response):
        if response.status_code != 200:
            raise Exception(f"FedoCal query issue: {response.json().get('message')}")

    async def _get_meetings(self):
        response = await self._get("meetings")
        self._check_errors(response)
        return response.json()["meetings"]

    async def _sortfilter_meetings(self):
        meetings = await self._get_meetings()
        now = datetime.utcnow()
        future_meetings = []
        for meeting in meetings:
            datetime_string = f"{meeting['meeting_date']} {meeting['meeting_time_start']}"
            start_time = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S")
            if now < start_time:
                future_meetings.append((start_time, meeting))
            else:
                continue
        return sorted(future_meetings, key=itemgetter(0))

    async def future_meetings(self, num=3):
        meetings = await self._sortfilter_meetings()
        response = ""
        for meeting in islice(meetings, 0, num):
            response = response + (
                f"- {meeting[1]['meeting_name']} (starting {arrow.get(meeting[0]).humanize()}){NL}"
            )
        if response == "":
            response = "There are no future meetings in FedoCal."
        return response

    async def next_room_meeting(self, room):
        meetings = await self._sortfilter_meetings()
        nextroom_meetings = [m for m in meetings if room in m[1].get("meeting_location", "")]
        if nextroom_meetings:
            date, meeting = nextroom_meetings[0]
            response = (
                f"The next meeting in this room ({room}) is: '{meeting['meeting_name']}' "
                f"(starting {arrow.get(date).humanize()})"
            )
        else:
            response = f"There are no future meetings in FedoCal for this room ({room})."
        return response
