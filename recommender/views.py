from typing import List
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .forms import MovieSearchForm

from django.templatetags.static import static

import csv
from datetime import datetime

featured_movie_list = [
    {
        "img_src": "https://images.thedirect.com/media/article_full/amazing-spider-man-3-andrew-garfield-movie-mcu.jpg",
        "img_alt": "...",
        "active": True
    },
    {
        "img_src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQqGllMkdIgITpxrpy33i0o_j3kHMAzUv6dVg&usqp=CAU",
        "img_alt": "...",
        "active": False
    },
    {
        "img_src": "https://1.bp.blogspot.com/-FjTt4fCZ1V8/W6l7PI-xrWI/AAAAAAAAPng/HFTsy7dqzdg5MsISmqgKNobfxYsqlo0NACLcBGAs/s1600/What%2Bare%2Byou%2Bwatching%253F.png",
        "img_alt": "...",
        "active": False
    },
    {
        "img_src": "https://static1.colliderimages.com/wordpress/wp-content/uploads/2022/11/avatar-the-way-of-water-poster.jpg",
        "img_alt": "...",
        "active": False
    }
]

DATA_FILE_PATH = './recommender/static/IMDB.csv'
TITLE = 'title'
RELEASE_DATE = 'release_date'
IMDB_RATING = 'imdb_rating'

# Create your views here.
def index(request):
    if request.method == 'POST':
        form = MovieSearchForm(request.POST)
        if form.is_valid():
            movie_list = _getIMDBMovieDataList()
            filtered_movie_list = _filter_imdb_movie_list(movie_list, form)
            context = {
                "featured_movies": featured_movie_list,
                "form": MovieSearchForm(),
                "filtered_movie_list": filtered_movie_list,
                "no_result_error": len(filtered_movie_list)==0
            }
            return render(request, 'index.html', context)
    context = {
        "featured_movies": featured_movie_list,
        "form": MovieSearchForm()
    }
    return render(request, 'index.html', context)


def _getIMDBMovieDataList():
    imdb_movie_list = []
    data_file = open(DATA_FILE_PATH, encoding = "utf8")
    csvreader = list(csv.reader(data_file))
    header_row = csvreader[0]
    title_idx = header_row.index(TITLE)
    release_date_idx = header_row.index(RELEASE_DATE)
    imdb_rating_idx = header_row.index(IMDB_RATING)
    for row in csvreader[1:]:
        imdbMovieData = IMDBMovieData(row[title_idx], row[imdb_rating_idx], row[release_date_idx])
        imdb_movie_list.append(imdbMovieData)
    data_file.close()
    return imdb_movie_list

def _filter_imdb_movie_list(imdb_movie_list, movie_search_form : MovieSearchForm):
    filtered_list = []
    for movie in imdb_movie_list:
        if movie.rating < movie_search_form.cleaned_data['imdb_rating']:
            continue
        if movie.release_date and movie.release_date.year != movie_search_form.cleaned_data['release_year']:
            continue
        filtered_list.append(movie)
    return filtered_list


class IMDBMovieData:

    def __init__(self, movie_title, rating, release_date) -> None:
        self.movie_title = movie_title
        try:
            self.rating = float(rating)
        except ValueError:
            self.rating = 0
        try:
            self.release_date = datetime.strptime(release_date, '%Y-%m-%d')
        except ValueError:
            self.release_date = None