from google.appengine.ext import ndb

from controllers.api.api_district_controller import ApiDistrictListController, ApiDistrictEventsController, ApiDistrictRankingsController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController, \
                                                 ApiEventMatchesController, ApiEventStatsController, \
                                                 ApiEventRankingsController, ApiEventAwardsController, ApiEventListController, ApiEventDistrictPointsController, ApiEventWeekController
from controllers.api.api_match_controller import ApiMatchController
from controllers.api.api_team_controller import ApiTeamController, ApiTeamEventsController, ApiTeamEventAwardsController, \
                                                ApiTeamEventMatchesController, ApiTeamMediaController, ApiTeamYearsParticipatedController, \
                                                ApiTeamListController

from models.event import Event
from models.event_team import EventTeam
from models.team import Team


class CacheClearer(object):
    @classmethod
    def get_award_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this award
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_list']
        years = affected_refs['year']

        return cls._get_event_awards_cache_keys_and_controllers(event_keys) + \
            cls._get_team_event_awards_cache_keys_and_controllers(team_keys, event_keys)

    @classmethod
    def get_event_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this event
        """
        event_keys = affected_refs['key']
        years = affected_refs['year']
        event_district_abbrevs = affected_refs['event_district_abbrev']

        event_team_keys_future = EventTeam.query(EventTeam.event.IN([event_key for event_key in event_keys])).fetch_async(None, keys_only=True)

        events_future = Event.query(Event.id.IN([event_key for event_key in event_keys])).fetch_async(None, projection=[Event.end_date, Event.start_date])

        team_keys = set()
        for et_key in event_team_keys_future.get_result():
            team_key_name = et_key.id().split('_')[1]
            team_keys.add(ndb.Key(Team, team_key_name))

        # Clear keys for live events. Normalize event starts to last monday
        time_indexes = set()
        for event in events_future.get_result():
            dt = event.start_date
            if dt.weekday() != 0:
                # If we're given a datetime for a non-Monday, normalize to that
                dt = dt + datetime.timedelta(days=(-1 * dt.weekday()))
            time_indexes.add(datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0))

        return cls._get_events_cache_keys_and_controllers(event_keys) + \
            cls._get_event_district_points_cache_keys_and_controllers(event_keys) + \
            cls._get_eventlist_cache_keys_and_controllers(years) + \
            cls._get_team_events_cache_keys_and_controllers(team_keys, years) + \
            cls._get_districtlist_cache_keys_and_controllers(years) + \
            cls._get_district_events_cache_keys_and_controllers(event_district_abbrevs, years) + \
            cls._get_district_rankings_cache_keys_and_controllers(event_district_abbrevs, years) + \
            cls._get_live_events_cache_keys_and_controllers(time_indexes)

    @classmethod
    def get_eventteam_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this eventteam
        """
        event_keys = affected_refs['event']
        team_keys = affected_refs['team']
        years = affected_refs['year']

        return cls._get_eventteams_cache_keys_and_controllers(event_keys) + \
            cls._get_team_events_cache_keys_and_controllers(team_keys, years) + \
            cls._get_team_years_participated_cache_keys_and_controllers(team_keys)

    @classmethod
    def get_match_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this match
        """
        match_keys = affected_refs['key']
        event_keys = affected_refs['event']
        team_keys = affected_refs['team_keys']
        years = affected_refs['year']

        return cls._get_match_cache_keys_and_controllers(match_keys) + \
            cls._get_matches_cache_keys_and_controllers(event_keys) + \
            cls._get_team_event_matches_cache_keys_and_controllers(team_keys, event_keys)

    @classmethod
    def get_media_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that reference this media
        """
        reference_keys = affected_refs['references']
        years = affected_refs['year']

        return cls._get_media_cache_keys_and_controllers(reference_keys, years)

    @classmethod
    def get_team_cache_keys_and_controllers(cls, affected_refs):
        """
        Gets cache keys and controllers that references this team
        """
        team_keys = affected_refs['key']

        event_team_keys_future = EventTeam.query(EventTeam.team.IN([team_key for team_key in team_keys])).fetch_async(None, keys_only=True)

        event_keys = set()
        for et_key in event_team_keys_future.get_result():
            event_key_name = et_key.id().split('_')[0]
            event_keys.add(ndb.Key(Event, event_key_name))

        return cls._get_teams_cache_keys_and_controllers(team_keys) + \
            cls._get_eventteams_cache_keys_and_controllers(event_keys) + \
            cls._get_teamlist_cache_keys_and_controllers(team_keys)

    @classmethod
    def _get_districtlist_cache_keys_and_controllers(cls, years):
        cache_keys_and_controllers = []
        for year in filter(None, years):
            cache_keys_and_controllers.append((ApiDistrictListController.get_cache_key_from_format(year), ApiDistrictListController))
        return cache_keys_and_controllers

    @classmethod
    def _get_district_events_cache_keys_and_controllers(cls, district_shorts, years):
        cache_keys_and_controllers = []
        for district_short in filter(None, district_shorts):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiDistrictEventsController.get_cache_key_from_format(district_short, year), ApiDistrictEventsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_district_rankings_cache_keys_and_controllers(cls, district_shorts, years):
        cache_keys_and_controllers = []
        for district_short in filter(None, district_shorts):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiDistrictRankingsController.get_cache_key_from_format(district_short, year), ApiDistrictRankingsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_event_awards_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventAwardsController.get_cache_key_from_format(event_key.id()), ApiEventAwardsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_event_district_points_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventDistrictPointsController.get_cache_key_from_format(event_key.id()), ApiEventDistrictPointsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_events_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventController.get_cache_key_from_format(event_key.id()), ApiEventController))
            cache_keys_and_controllers.append((ApiEventStatsController.get_cache_key_from_format(event_key.id()), ApiEventStatsController))
            cache_keys_and_controllers.append((ApiEventRankingsController.get_cache_key_from_format(event_key.id()), ApiEventRankingsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_live_events_cache_keys_and_controllers(cls, time_indexes):
        # time_indexes is a list of timestamps of Mondays at 0:00 UTC
        cache_keys_and_controllers = []
        for time_index in time_indexes:
            cache_keys_and_controllers.append((ApiEventWeekController.get_cache_key_from_format(time_index), ApiEventWeekController))
        return cache_keys_and_controllers

    @classmethod
    def _get_eventlist_cache_keys_and_controllers(cls, years):
        cache_keys_and_controllers = []
        for year in filter(None, years):
            cache_keys_and_controllers.append((ApiEventListController.get_cache_key_from_format(year), ApiEventListController))
        return cache_keys_and_controllers

    @classmethod
    def _get_eventteams_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventTeamsController.get_cache_key_from_format(event_key.id()), ApiEventTeamsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_match_cache_keys_and_controllers(cls, match_keys):
        cache_keys_and_controllers = []
        for match_key in filter(None, match_keys):
            cache_keys_and_controllers.append((ApiMatchController.get_cache_key_from_format(match_key.id()), ApiMatchController))
        return cache_keys_and_controllers

    @classmethod
    def _get_matches_cache_keys_and_controllers(cls, event_keys):
        cache_keys_and_controllers = []
        for event_key in filter(None, event_keys):
            cache_keys_and_controllers.append((ApiEventMatchesController.get_cache_key_from_format(event_key.id()), ApiEventMatchesController))
        return cache_keys_and_controllers

    @classmethod
    def _get_media_cache_keys_and_controllers(cls, team_keys, years):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiTeamMediaController.get_cache_key_from_format(team_key.id(), year), ApiTeamMediaController))
        return cache_keys_and_controllers

    @classmethod
    def _get_teams_cache_keys_and_controllers(cls, team_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            cache_keys_and_controllers.append((ApiTeamController.get_cache_key_from_format(team_key.id()), ApiTeamController))
        return cache_keys_and_controllers

    @classmethod
    def _get_team_event_awards_cache_keys_and_controllers(cls, team_keys, event_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for event_key in filter(None, event_keys):
                cache_keys_and_controllers.append((ApiTeamEventAwardsController.get_cache_key_from_format(team_key.id(), event_key.id()), ApiTeamEventAwardsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_team_event_matches_cache_keys_and_controllers(cls, team_keys, event_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for event_key in filter(None, event_keys):
                cache_keys_and_controllers.append((ApiTeamEventMatchesController.get_cache_key_from_format(team_key.id(), event_key.id()), ApiTeamEventMatchesController))
        return cache_keys_and_controllers

    @classmethod
    def _get_team_events_cache_keys_and_controllers(cls, team_keys, years):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            for year in filter(None, years):
                cache_keys_and_controllers.append((ApiTeamEventsController.get_cache_key_from_format(team_key.id(), year), ApiTeamEventsController))
        return cache_keys_and_controllers

    @classmethod
    def _get_team_years_participated_cache_keys_and_controllers(cls, team_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            cache_keys_and_controllers.append((ApiTeamYearsParticipatedController.get_cache_key_from_format(team_key.id()), ApiTeamYearsParticipatedController))
        return cache_keys_and_controllers

    @classmethod
    def _get_teamlist_cache_keys_and_controllers(cls, team_keys):
        cache_keys_and_controllers = []
        for team_key in filter(None, team_keys):
            page_num = int(team_key.id()[3:]) / ApiTeamListController.PAGE_SIZE
            cache_keys_and_controllers.append((ApiTeamListController.get_cache_key_from_format(page_num), ApiTeamListController))
        return cache_keys_and_controllers
