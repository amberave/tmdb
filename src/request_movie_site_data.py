import requests
from bs4 import BeautifulSoup
import json
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

def search_tmdb(query, year):
    search = tmdb.Search()
    response = search.movie(query=query, year=year)
    try:
        return search.results[0]["id"]
    except:
        return None

def retrieve_tmdb_data(movie_dict, tmdb_id):
    # print("Info retrieved!")
    movie = tmdb.Movies(tmdb_id)

    response = movie.credits()
    directors = [] 
    for credit in movie.crew:  
        if credit["job"] == "Director":  
            directors.append(credit["name"])
    movie_dict["Director"] =     ', '.join(directors)

    # get basic movie info
    response = movie.info()
    movie_dict["Runtime (minutes)"] = movie.runtime
    movie_dict["Budget"] = movie.budget
    movie_dict["Box Office"] = movie.revenue
    imdb_id = movie.imdb_id
    movie_dict["Country of Origin"] = movie.origin_country[0]

    # get classification
    response = movie.releases()
    for c in movie.countries:
        if c['iso_3166_1'] == 'AU':
            movie_dict["Classification"] = c['certification']
    
    # putting this last as IMDb data will be next columns
    movie_dict["IMDb ID"] = imdb_id
    
    return movie_dict

def search_imdb(movie_dict):
    # Credit: https://imdbapi.dev/
    imdb_id = movie_dict["IMDb ID"] if "IMDb ID" in movie_dict.keys() else None
    if type(imdb_id) is not str:
        return None, None
    url = "https://api.imdbapi.dev/titles/" + imdb_id

    headers = {"accept": "application/xml"}
    try:
        response = requests.get(url, headers=headers, timeout=3)
    except requests.exceptions.ReadTimeout:
        return None, None
    return response.status_code, response.json()

def scrape_rotten_tomatoes(title, year, full_cast:list):
    # Credit: https://github.com/placson/rottenmovies/blob/main/rotten.py
    rt_data = {} # write info to dict
    cleaned_title = ''.join([c if c.isalnum() else ' ' if c == ' ' or '.' else '' for c in str(title) ])
    MOVIE_SEARCH_URL = "https://www.rottentomatoes.com/search?search=%s" 
    movie_url = MOVIE_SEARCH_URL % cleaned_title
    
    response = requests.get(movie_url)
    rt_response_html = BeautifulSoup(response.content, 'html.parser')
    movie_results = rt_response_html.find_all('search-page-result',type='movie')
    movie_results = BeautifulSoup(str(movie_results),'html.parser')
    movie_rows = movie_results.find_all('search-page-media-row')    
    for movie_row in movie_rows:
        releaseYear = int(movie_row['release-year'])
        href = movie_row.find('a',slot='title')
        rt_title = href.text.strip()
        cast = movie_row['cast']
        # print(f"{year}: {releaseYear}")
        # print(f"{title}: {rt_title}")
        # print(f"{cast.split(',')}: {full_cast[:4]}")
        # print(int(year) in range(releaseYear-1, releaseYear+2) and (rt_title == title or set(cast.split(',')).issubset(set(full_cast))))
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
            #print(f"Break: {cast}")
            print(rt_data)

            return rt_data
        #print(f"{rt_title} ({releaseYear})")
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
        print("Letterboxd data not available")
        return letterboxd_data
    
    for result in search_data["results"]:
        # allow for a 1-year difference
        if result["year"] in range(year-1, year+2):
            slug = result["slug"]
            break

    if slug:
        movie = Movie(slug)
        letterboxd_data["Letterboxd Average Rating"] = movie.rating
        letterboxd_data["Cast (from Letterboxd)"] = ', '.join([entry["name"].replace(',', '') for entry in movie.cast])
        letterboxd_data["Letterboxd My Rating"] = (user_ratings["movies"][slug]["rating"] if slug in user_ratings["movies"] else None) 
        letterboxd_data["Letterboxd Review Count"] = movie.pages.profile.script["aggregateRating"]["reviewCount"] 
        letterboxd_data["Letterboxd Rating Count"] = movie.pages.profile.script["aggregateRating"]["ratingCount"] 
    print(letterboxd_data)

    return letterboxd_data
    
