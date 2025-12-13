import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import tmdbsimple as tmdb
from letterboxdpy.user import User
from letterboxdpy.movie import Movie
from letterboxdpy.search import Search

def setup_apis():
    # set up TMDB API
    with open("api_key.txt", 'r') as f:
        api_key = f.read()
    
    tmdb.API_KEY = api_key
    tmdb.REQUESTS_TIMEOUT = 5  # seconds, for both connect and read
    tmdb.REQUESTS_SESSION = requests.Session()

    return tmdb

def search_tmdb(query, year, medium):
    search = tmdb.Search()
    response = search.tv(query=query, year=year) if medium in ['Documentary Mini Series', 'Mini Series'] else search.movie(query=query, year=year)
    try:
        return search.results[0]["id"]
    except:
        return None

def retrieve_tmdb_data(movie_dict, tmdb_id, medium):
    is_tv = medium in ['Documentary Mini Series', 'Mini Series']
    item = tmdb.TV(tmdb_id) if is_tv else tmdb.Movies(tmdb_id)

    try:
        response = item.credits()
    except:
        return movie_dict
    directors = [] 
    for credit in item.crew:  
        if credit["job"] == "Director":  
            directors.append(credit["name"])
    movie_dict["Director"] =     ', '.join(directors)

    # get basic movie info
    response = item.info()
    
    if not is_tv:
        movie_dict["Runtime (minutes)"] = item.runtime
        movie_dict["Budget"] = item.budget
        movie_dict["Box Office"] = item.revenue
        imdb_id = item.imdb_id
        movie_dict["Franchise"] = item.belongs_to_collection["name"].replace(' Collection', '') if item.belongs_to_collection is not None and movie_dict["Franchise"] is None else movie_dict["Franchise"]
    
    movie_dict["Country of Origin"] = ', '.join(item.origin_country)
    movie_dict["Spoken Languages"] = ', '.join(country["english_name"] for country in item.spoken_languages)
    
    # get classification
    if not is_tv:
        response = item.releases()
        # tries to retrieve AUS classification, but will return US class if AUS not found
        us_class = ''
        aus_class = ''
        for c in item.countries:
            if c['iso_3166_1'] == 'AU':
                aus_class = c['certification']
                break
            if c['iso_3166_1'] == 'US':
                us_class = c['certification']
        movie_dict["Classification"] = aus_class if aus_class != '' else f"{us_class} (US)" if us_class != '' else None

        # putting this last as IMDb data will be next columns
        movie_dict["IMDb ID"] = imdb_id
    
    return movie_dict

def search_imdb(movie_dict):
    # Credit: https://imdbapi.dev/
    imdb_data = {}
    imdb_id = movie_dict["IMDb ID"] if "IMDb ID" in movie_dict.keys() and movie_dict["IMDb ID"] is not None else movie_dict["IMDb ID (from Letterboxd)"] if "IMDb ID (from Letterboxd)" in movie_dict.keys() else None
    if type(imdb_id) is not str:
        return imdb_data
    url = "https://api.imdbapi.dev/titles/" + imdb_id

    headers = {"accept": "application/xml"}
    try:
        response = requests.get(url, headers=headers, timeout=3)
    except Exception:
        return imdb_data
    
    if response.status_code == 200:
        imdb_response = response.json()
        imdb_data["IMDb Rating"] = imdb_response["rating"]["aggregateRating"]
        try:
            imdb_data["Metascore"] = imdb_response["metacritic"]["score"]
        except:
            # if not present, no entry on Metacritic
            imdb_data["Metascore"] = "Not Listed"
        imdb_data["Poster URL"] = imdb_response["primaryImage"]["url"]

    return imdb_data

def scrape_rotten_tomatoes(title, year, medium, full_cast:list):
    # Credit: https://github.com/placson/rottenmovies/blob/main/rotten.py
    rt_data = {} # write info to dict
    cleaned_title = ''.join([c if c.isalnum() else ' ' if c == ' ' or '.' else '' for c in str(title) ])
    medium_type = ("tvSeries" if medium in ['Documentary Mini Series', 'Mini Series'] else "movie")
    release_year_str = ("startyear" if medium in ['Documentary Mini Series', 'Mini Series'] else "release-year")

    MOVIE_SEARCH_URL = "https://www.rottentomatoes.com/search?search=%s" 
    movie_url = MOVIE_SEARCH_URL % cleaned_title
    
    response = requests.get(movie_url)
    rt_response_html = BeautifulSoup(response.content, 'html.parser')
    movie_results = rt_response_html.find_all('search-page-result',type=medium_type)
    movie_results = BeautifulSoup(str(movie_results),'html.parser')
    movie_rows = movie_results.find_all('search-page-media-row')    
    for movie_row in movie_rows:
        releaseYear = int(movie_row[release_year_str]) if movie_row[release_year_str].isdigit() else None
        if releaseYear is None:
            continue
        href = movie_row.find('a',slot='title')
        rt_title = href.text.strip()
        cast = movie_row['cast']
        # allow for year to be one more/one less in case of inconsistencies
        if int(year) in range(releaseYear-1, releaseYear+2) and (rt_title == title or set(cast.split(',')).issubset(set(full_cast))):
            # rt_data["Cast"] = cast

            # fetch details by going deeper into the exact movie link
            link = href['href'].strip()
            response = requests.get(link)
            rt_response_html = BeautifulSoup(response.content, 'html.parser')
            
            # aggregate json (embedded in script at the top of the page)
            agg_json = rt_response_html.find('script', type="application/ld+json").text.strip()
            
            # media scorecard json (embedded in script)
            scorecard_json = rt_response_html.find('script', id="media-scorecard-json").text.strip()
            scorecard = json.loads(scorecard_json)

            # criticsScore (tomatometer)
            critics_score = scorecard['criticsScore']
            if 'score' in critics_score:
                tomato_score = critics_score['score']
                rt_data["Tomatometer (Critic Score)"] = tomato_score
            else:
                rt_data["Tomatometer (Critic Score)"] = "Not Listed"

            # audienceScore (popcorn meter)
            pop_score = scorecard['audienceScore']
            if 'score' in pop_score:
                popcorn_score = pop_score['score']
                rt_data["Popcornmeter (Audience Score)"] = popcorn_score
            else:
                rt_data["Popcornmeter (Audience Score)"] = "Not Listed"

            # once film with correct title and year found, return its info
            return rt_data
    return rt_data

def get_letterboxd_user_ratings(username: str):
    # Credit: https://github.com/nmcassa/letterboxdpy
    user_instance = User(username)
    args = {}
    method = User.get_films
    if isinstance(method, list):
        method, args = method
    data = method(user_instance, **args) if args else method(user_instance)
    return data

def get_letterboxd_movie_data(title: str, year, user_ratings: dict):
    # Credit: https://github.com/nmcassa/letterboxdpy
    letterboxd_data = {}
    year = int(year)
    slug = ""

    search_instance = Search(str(title).replace('/', ' '), "films")
    #try:
    search_data = search_instance.results
    #except Exception as e:
     
        # return letterboxd_data
    
    if not search_data["available"]:
        return letterboxd_data
    
    for result in search_data["results"]:
        # allow for a 1-year difference
        if result["year"] in range(year-1, year+2):
            slug = result["slug"]
            break

    if slug:
        movie = Movie(slug)
        letterboxd_data["Letterboxd Average Rating"] = movie.rating
        movie_logged = slug in user_ratings["movies"]
        letterboxd_data["Letterboxd My Rating"] = (float(user_ratings["movies"][slug]["rating"])/2 if movie_logged and user_ratings["movies"][slug]["rating"] is not None else "Not Rated" if movie_logged else None) 
        letterboxd_data["Letterboxd Review Count"] = movie.pages.profile.script["aggregateRating"]["reviewCount"] 
        letterboxd_data["Letterboxd Rating Count"] = movie.pages.profile.script["aggregateRating"]["ratingCount"] 
        letterboxd_data["Cast (from Letterboxd)"] = ', '.join([entry["name"].replace(',', '') for entry in movie.cast])
        letterboxd_data["Runtime (from Letterboxd)"] = movie.runtime
        letterboxd_data["TMDB ID (from Letterboxd)"] = movie.tmdb_link.rsplit('/', 2)[1]
        letterboxd_data["IMDb ID (from Letterboxd)"] = movie.imdb_link.rsplit('/', 2)[1]

    return letterboxd_data
    
def get_oscars_data(imdb_id, year):
    oscars_data = {}
    award_url = "https://web-production-b8145.up.railway.app/awards/imdb/" + imdb_id
    awards_response = requests.get(award_url)
    if awards_response.status_code == 200:
        awards_json = awards_response.json()
        oscars_data["Academy Award Nominations"] = len(awards_json)
        
        num_wins = 0
        nom_list = []
        for nom in awards_json:
            category = nom["category"]
            nominees = ', '.join([entry["name"].replace(",", '').replace(";", '').replace(":", '') for entry in nom["names"]])
            if nom["isWinner"] == "1": 
                num_wins += 1
                nom_list.append(f"{category}; {nominees}; Winner")
            else:
                nom_list.append(f"{category}; {nominees}; Nominee")
        
        oscars_data["Academy Award Wins"] = num_wins
        oscars_data["Academy Award Details"] = ':'.join([str(details) for details in nom_list])

    # if no details retrieved, movie probably did not get nominated
    if not oscars_data:
        oscars_data["Academy Award Nominations"] = 0
        oscars_data["Academy Award Wins"] = 0
    
        # if movie was released more than 2 yrs ago, it will not receive any awards
        # fill these with empty string so program skips them next time
        if year < datetime.now().year - 2:
            oscars_data["Academy Award Details"] = ''

    return oscars_data