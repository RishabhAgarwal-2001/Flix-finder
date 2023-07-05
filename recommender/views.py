from collections import defaultdict
from typing import List
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from .forms import MovieSearchForm

from django.templatetags.static import static

import csv
import json
import random
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

IMDB_DATA_FILE_PATH = './recommender/static/IMDB.csv'
ROTTEN_TOMATO_DATA_FILE_PATH = './recommender/static/rtm.json'
TITLE = 'title'
RELEASE_DATE = 'release_date'
IMDB_RATING = 'imdb_rating'

# Create your views here.
def index(request):
    if request.method == 'POST':
        form = MovieSearchForm(request.POST)
        if form.is_valid():
            imdb_movie_list = _getIMDBMovieDataList()
            rotten_tomato_movie_list = _getRottenTomatoMovieDataList()
            filtered_imdb_movie_list = _filter_imdb_movie_list(imdb_movie_list, form)
            filtered_rotten_tomato_movie_list = _filter_rotten_tomato_movie_list(rotten_tomato_movie_list, form)
            merged_list = _merge_movie_lists(filtered_imdb_movie_list, filtered_rotten_tomato_movie_list, form)
            merged_list.sort(key=lambda obj: (
                obj.imdb_rating is not None and obj.rtm_rating is not None, 
                obj.imdb_rating is None, 
                obj.rtm_rating is None
            ))
            context = {
                "featured_movies": _getPosterImages(),
                "form": MovieSearchForm(),
                "filtered_movie_list": merged_list,
                "no_result_error": len(merged_list)==0
            }
            return render(request, 'index.html', context)
    context = {
        "featured_movies": featured_movie_list,
        "form": MovieSearchForm()
    }
    return render(request, 'index.html', context)

def _getPosterImages(count = 3):
    return featured_movie_list

def _getIMDBMovieDataList():
    imdb_movie_list = []
    data_file = open(IMDB_DATA_FILE_PATH, encoding="utf8")
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

def _getRottenTomatoMovieDataList():
    rotten_tomato_movie_list = []
    data_file = open(ROTTEN_TOMATO_DATA_FILE_PATH, encoding="utf8")
    json_data = json.load(data_file)
    for movie_json_data in json_data:
        if 'movieName' not in movie_json_data:
            continue
        rotten_tomato_movie_data = RottenTomatoMovieData(movie_json_data['movieName'], movie_json_data['movieRating'], movie_json_data['movieYear'])
        rotten_tomato_movie_list.append(rotten_tomato_movie_data)
    data_file.close()
    return rotten_tomato_movie_list

def _filter_imdb_movie_list(imdb_movie_list, movie_search_form : MovieSearchForm):
    filtered_list = []
    for movie in imdb_movie_list:
        if movie.rating < movie_search_form.cleaned_data['imdb_rating']:
            continue
        if movie.release_date and movie.release_date.year != movie_search_form.cleaned_data['release_year']:
            continue
        filtered_list.append(movie)
    return filtered_list

def _filter_rotten_tomato_movie_list(rotten_tomato_movie_list, movie_search_form: MovieSearchForm):
    filtered_list = []
    for movie in rotten_tomato_movie_list:
        if movie_search_form.cleaned_data['rotten_tomato_rating'] and movie.rating < movie_search_form.cleaned_data['rotten_tomato_rating']:
            continue
        if movie.release_year and movie.release_year != movie_search_form.cleaned_data['release_year']:
            continue
        filtered_list.append(movie)
    return filtered_list


def _merge_movie_lists(imdb_movie_list, rtm_movie_list, form: MovieSearchForm):
    merged_movie_list = []
    movie_name_movie_year_to_movie_data = defaultdict(lambda: {})
    for imdb_movie in imdb_movie_list:
        movie_name = imdb_movie.movie_title
        imdb_rating = imdb_movie.rating
        rtm_rating = None
        release_year = imdb_movie.release_date.year
        movie_name_movie_year_to_movie_data[movie_name.lower()][release_year] = MovieData(movie_name, imdb_rating, rtm_rating, release_year)
    for rtm_movie in rtm_movie_list:
        movie_name = rtm_movie.movie_title
        rtm_rating = rtm_movie.rating
        imdb_rating = None
        release_year = rtm_movie.release_year
        existing_object = movie_name_movie_year_to_movie_data[movie_name.lower()].get(release_year, None)
        if not existing_object:
            movie_name_movie_year_to_movie_data[movie_name.lower()][release_year] = MovieData(movie_name, imdb_rating, rtm_rating, release_year)
        else:
            existing_object.rtm_rating = rtm_rating
            movie_name_movie_year_to_movie_data[movie_name.lower()][release_year] = existing_object
    for movie_year_to_movie_data in movie_name_movie_year_to_movie_data.values():
        for movie_data in movie_year_to_movie_data.values():
            if not form.cleaned_data['include_empty_rotten_tomato_ratings'] and movie_data.rtm_rating is None:
                continue
            if not form.cleaned_data['include_empty_imdb_ratings'] and movie_data.imdb_rating is None:
                continue
            merged_movie_list.append(movie_data)
    print(merged_movie_list)
    return merged_movie_list

class MovieData:
    def __init__(self, movie_title, imdb_rating, rtm_rating, release_year):
        self.movie_title = movie_title
        self.imdb_rating = imdb_rating
        self.rtm_rating = rtm_rating
        self.release_year = release_year
    def __str__(self) -> str:
        return f"{self.movie_title} {self.imdb_rating} {self.rtm_rating} {self.release_year}"

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

class RottenTomatoMovieData:
    def __init__(self, movie_title, rating, release_year) -> None:
        self.movie_title = movie_title
        try: 
            self.rating = float(rating.strip('%')) / 10
        except ValueError:
            self.rating = 0
        try:
            self.release_year = int(release_year)
        except ValueError:
            self.release_year = None
