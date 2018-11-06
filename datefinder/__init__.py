import copy
import logging
import regex as re
from dateutil import tz, parser

from .constants import REPLACEMENTS, TIMEZONE_REPLACEMENTS, STRIP_CHARS, DATE_REGEX, RANGE_REGEX

logger = logging.getLogger('datefinder')


class DateFinder(object):
    """
    Locates dates in a text
    """

    def __init__(self, base_date=None):
        self.base_date = base_date

    def find_dates(self, text, source=False, index=False, capture=False, strict=False):

        # Append text with a delimiter to make inputs consisting of solely a date work
        text = text + ' '

        for date_string, indices, captures in self.extract_date_strings(text, strict=strict):

            as_dt = self.parse_date_string(date_string, captures)
            if as_dt is None:
                # Dateutil couldn't make heads or tails of it
                # move on to next
                continue

            returnables = (as_dt,)
            if source:
                returnables = returnables + (date_string,)
            if index:
                returnables = returnables + (indices,)
            if capture:
                returnables = returnables + (captures,)
            if len(returnables) == 1:
                returnables = returnables[0]
            yield returnables

    def _find_and_replace(self, date_string, captures):
        """
        :warning: when multiple tz matches exist the last sorted capture will trump
        :param date_string:
        :return: date_string, tz_string
        """
        # add timezones to replace
        cloned_replacements = copy.copy(REPLACEMENTS)  # don't mutate
        for tz_string in captures.get('timezones', []):
            cloned_replacements.update({tz_string: ' '})

        date_string = date_string.lower()
        for key, replacement in cloned_replacements.items():
            # we really want to match all permutations of the key surrounded by whitespace chars except one
            # for example: consider the key = 'to'
            # 1. match 'to '
            # 2. match ' to'
            # 3. match ' to '
            # but never match r'(\s|)to(\s|)' which would make 'october' > 'ocber'
            date_string = re.sub(r'(^|\s)' + key + r'(\s|$)', replacement, date_string, flags=re.IGNORECASE)

        return date_string, self._pop_tz_string(sorted(captures.get('timezones', [])))

    def _pop_tz_string(self, list_of_timezones):
        try:
            tz_string = list_of_timezones.pop()
            # make sure it's not a timezone we
            # want replaced with better abbreviation
            return TIMEZONE_REPLACEMENTS.get(tz_string, tz_string)
        except IndexError:
            return ''

    def _add_tzinfo(self, datetime_obj, tz_string):
        """
        take a naive datetime and add dateutil.tz.tzinfo object

        :param datetime_obj: naive datetime object
        :return: datetime object with tzinfo
        """
        if datetime_obj is None:
            return None

        tzinfo_match = tz.gettz(tz_string)
        return datetime_obj.replace(tzinfo=tzinfo_match)

    def parse_date_string(self, date_string, captures):
        # For well formatted string, we can already let dateutils parse them
        # otherwise self._find_and_replace method might corrupt them
        try:
            as_dt = parser.parse(date_string, default=self.base_date)
        except ValueError:
            # replace tokens that are problematic for dateutil
            date_string, tz_string = self._find_and_replace(date_string, captures)

            ## One last sweep after removing
            date_string = date_string.strip(STRIP_CHARS)
            ## Match strings must be at least 3 characters long
            ## < 3 tends to be garbage
            if len(date_string) < 3:
                return None

            try:
                logger.debug('Parsing {0} with dateutil'.format(date_string))
                as_dt = parser.parse(date_string, default=self.base_date)
            except Exception as e:
                logger.debug(e)
                as_dt = None
            if tz_string:
                as_dt = self._add_tzinfo(as_dt, tz_string)
        return as_dt

    def extract_date_strings(self, text, strict=False):
        """
        Scans text for possible datetime strings and extracts them
        :param strict: Strict mode will only return dates sourced with day, month, and year
        """
        # Begin by trying to match ranges
        for match in DATE_REGEX.finditer(text):
            match_str = match.group(0)
            indices = match.span(0)

            # Check if we match a range too
            found_range = False
            range_strings = []
            for range_match in RANGE_REGEX.finditer(match_str):
                # Parse date 1 and date 2 recursively
                range_captures = range_match.capturesdict()
                date_1 = range_captures.get("date_1", [])
                date_2 = range_captures.get("date_2", [])

                for date_1_str in date_1:
                    range_strings.extend(self.extract_date_strings(date_1_str, strict=strict))

                for date_2_str in date_2:
                    range_strings.extend(self.extract_date_strings(date_2_str, strict=strict))


            for range_string in range_strings:
                yield range_string

            if not found_range:
                ## Get individual group matches
                captures = match.capturesdict()
                time = captures.get('time')
                digits = captures.get('digits')
                digits_modifiers = captures.get('digits_modifiers')
                days = captures.get('days')
                months = captures.get('months')
                timezones = captures.get('timezones')
                delimiters = captures.get('delimiters')
                time_periods = captures.get('time_periods')
                extra_tokens = captures.get('extra_tokens')

                if delimiters and match_str.endswith(delimiters[-1]):
                    captures['delimiters'] = captures['delimiters'][:-1]

                if strict:
                    complete = False
                    ## 12-05-2015
                    if len(digits) == 3:
                        complete = True
                        ## 19 February 2013 year 09:10
                    elif (len(months) == 1) and (len(digits) == 2):
                        complete = True
                        
                    if not complete:
                        continue

                ## sanitize date string
                ## replace unhelpful whitespace characters with single whitespace
                match_str = re.sub(r'[\n\t\s\xa0]+', ' ', match_str)
                match_str = match_str.strip(STRIP_CHARS)

                ## Save sanitized source string
                yield match_str, indices, captures


def find_dates(
    text,
    source=False,
    index=False,
    capture=False,
    strict=False,
    base_date=None
    ):
    """
    Extract datetime strings from text

    :param text:
        A string that contains one or more natural language or literal
        datetime strings
    :type text: str|unicode
    :param source:
        Return the original string segment
    :type source: boolean
    :param index:
        Return the indices where the datetime string was located in text
    :type index: boolean
    :param strict:
        Only return datetimes with complete date information. For example:
        `July 2016` of `Monday` will not return datetimes.
        `May 16, 2015` will return datetimes.
    :type strict: boolean
    :param base_date:
        Set a default base datetime when parsing incomplete dates
    :type base_date: datetime

    :return: Returns a generator that produces :mod:`datetime.datetime` objects,
        or a tuple with the source text and index, if requested
    """
    date_finder = DateFinder(base_date=base_date)
    return date_finder.find_dates(text, source=source, index=index, capture=capture, strict=strict)
