from datetime import datetime, timedelta

from django import forms
from django.db.models import Q
from django.db.models.sql.constants import QUERY_TERMS
from django.utils.translation import ugettext as _

from filter.fields import RangeField, LookupTypeField

__all__ = [
    'Filter', 'CharFilter', 'BooleanFilter', 'ChoiceFilter', 
    'MultipleChoiceFilter', 'DateFilter', 'DateTimeFilter', 'TimeFilter', 
    'ModelChoiceFilter', 'ModelMultipleChoiceFilter', 'NumberFilter', 
    'RangeFilter', 'DateRangeFilter'
]

LOOKUP_TYPES = sorted(QUERY_TERMS.keys())

class Filter(object):
    creation_counter = 0
    field = forms.Field
    
    def __init__(self, name=None, label=None, widget=None, action=None, 
        lookup_type='exact', **kwargs):
        self.name = name
        self.label = label
        if action:
            self.filter = action
        self.lookup_type = lookup_type
        
        if self.lookup_type is None or isinstance(self.lookup_type, (list, tuple)):
            if lookup_type is None:
                lookup = [(x, x) for x in LOOKUP_TYPES]
            else:
                lookup = [(x, x) for x in LOOKUP_TYPES if x in self.lookup_type]
            self.field = LookupTypeField(self.field(required=False, widget=widget, **kwargs), lookup, required=False, label=label)
        else:
            self.field = self.field(required=False, label=label, widget=widget, **kwargs)

        
        self.extra = kwargs
        
        self.creation_counter = Filter.creation_counter
        Filter.creation_counter += 1
    
    def filter(self, qs, value):
        if value:
            if isinstance(value, (list, tuple)):
                lookup = str(value[1])
                value = value[0]
            else:
                lookup = self.lookup_type
            return qs.filter(**{'%s__%s' % (self.name, lookup): value})
        return qs
        
class CharFilter(Filter):
    field = forms.CharField

class BooleanFilter(Filter):
    field = forms.NullBooleanField
    
    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{self.name: value})
        return qs

class ChoiceFilter(Filter):
    field = forms.ChoiceField

class MultipleChoiceFilter(Filter):
    """
    This filter preforms an OR query on the selected options.
    """
    field = forms.MultipleChoiceField
    
    def filter(self, qs, value):
        q = Q()
        for v in value:
            q |= Q(**{self.name: v})
        return qs.filter(q).distinct()

class DateFilter(Filter):
    field = forms.DateField

class DateTimeFilter(Filter):
    field = forms.DateTimeField

class TimeFilter(Filter):
    field = forms.TimeField

class ModelChoiceFilter(Filter):
    field = forms.ModelChoiceField

class ModelMultipleChoiceFilter(MultipleChoiceFilter):
    field = forms.ModelMultipleChoiceField

class NumberFilter(Filter):
    field = forms.DecimalField

class RangeFilter(Filter):
    field = RangeField
    
    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__range' % self.name: (value.start, value.stop)})
        return qs

class DateRangeFilter(ChoiceFilter):
    options = {
        1: (_('Any Date'), lambda qs, name: qs.all()),
        2: (_('Today'), lambda qs, name: qs.filter(**{
            '%s__year' % name: datetime.today().year, 
            '%s__month' % name: datetime.today().month, 
            '%s__day' % name: datetime.today().day
        })),
        3: (_('Past 7 days'), lambda qs, name: qs.filter(**{
            '%s__gte' % name: (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'),
            '%s__lte' % name: datetime.today().strftime('%Y-%m-%d'),
        })),
        4: (_('This month'), lambda qs, name: qs.filter(**{
            '%s__year' % name: datetime.today().year,
            '%s__month' % name: datetime.today().month
        })),
        5: (_('This year'), lambda qs, name: qs.filter(**{
            '%s__year' % name: datetime.today().year,
        })),
    }
    
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [(key, value[0]) for key, value in self.options.iteritems()]
        super(DateRangeFilter, self).__init__(*args, **kwargs)
    
    def filter(self, qs, value):
        return self.options[int(value)][1](qs, self.name)
