from django import forms

from .models import CountRangeTract

# widget=forms.HiddenInput())
class SelectedCensusTractForm(forms.Form):
    #agg_type = forms.CharField(initial="SomeType")
    #id = forms.IntegerField(initial=23)
    #map_bbox = forms.CharField(initial="a=b")
    agg_type = forms.CharField()
    id = forms.IntegerField(label="Db ID")
    range_count = forms.IntegerField(label="Total IP Ranges")
    map_bbox = forms.CharField(widget=forms.HiddenInput())

    # Range count doesn't work for IP ranges (looks like a single range, really many)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agg_type'].widget.attrs['readonly'] = True
        self.fields['id'].widget.attrs['readonly'] = True
        self.fields['range_count'].widget.attrs['readonly'] = True
        self.fields['map_bbox'].widget.attrs['readonly'] = True
