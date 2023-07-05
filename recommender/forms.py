from django import forms

class MovieSearchForm(forms.Form):
    imdb_rating = forms.DecimalField(min_value=0.0, max_value=9.9, label='Minimum IMDB Rating')
    rotten_tomato_rating = forms.DecimalField(min_value=0.0, max_value=9.9, label='Minimum Rotten Tomato Rating')
    include_empty_rotten_tomato_ratings = forms.BooleanField(required=False, initial=False)
    include_empty_imdb_ratings = forms.BooleanField(required=False, initial=False)
    release_year = forms.IntegerField(required=True)
