from django import forms

from .models import CountRangeTract

# widget=forms.HiddenInput())
class SelectedCensusTractForm(forms.Form):
    agg_type = forms.CharField(initial="SomeType")
    id = forms.IntegerField(initial=23)
    map_bbox = forms.CharField(initial="a=b")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agg_type'].widget.attrs['readonly'] = True
        self.fields['id'].widget.attrs['readonly'] = True
        # self.fields['map_bbox'].widget.attrs['readonly'] = True
