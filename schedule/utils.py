import datetime
import heapq


class EventListManager(object):
    """
    This class is responsible for doing functions on a list of events. It is
    used to when one has a list of events and wants to access the occurrences
    from these events in as a group
    """
    def __init__(self, events):
        self.events = events
    
    def occurrences_after(self, after=None):
        """
        It is often useful to know what the next occurrence is given a list of
        events.  This function produces a generator that yields the 
        the most recent occurrence after the date ``after`` from any of the
        events in ``self.events``
        """
        from schedule.models import Occurrence
        if after is None:
            after = datetime.datetime.now()
        occ_replacer = OccurrenceReplacer(
            Occurrence.objects.filter(event__in = self.events))
        generators = [event._occurrences_after_generator(after) for event in self.events]
        occurrences = []
        
        for generator in generators:
            try:
                heapq.heappush(occurrences, (generator.next(), generator))
            except StopIteration:
                pass
        
        while True:
            if len(occurrences) == 0: raise StopIteration
            
            generator=occurrences[0][1]
            
            try:
                next = heapq.heapreplace(occurrences, (generator.next(), generator))[0]
            except StopIteration:
                next = heapq.heappop(occurrences)
            yield occ_replacer.get_occurrence(next)
    

class OccurrenceReplacer(object):
    """
    When getting a list of occurrences, the last thing that needs to be done
    before passing it forward is to make sure all of the occurrences that
    have been stored in the datebase replace, in the list you are returning,
    the generated ones that are equivalent.  This class makes this easier.
    """
    def __init__(self, persisted_occurrences):
        lookup = [((occ.event, occ.original_start, occ.original_end), occ) for 
            occ in persisted_occurrences]
        self.lookup = dict(lookup)
    
    def get_occurrence(self, occ):
        return self.lookup.get(
            (occ.event, occ.original_start, occ.original_end),
            occ)
    
    def has_occurrence(self, occ):
        return (occ.event, occ.original_start, occ.original_end) in self.lookup
        