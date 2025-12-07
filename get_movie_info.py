import requests
import tmdbsimple as tmdb
import pandas as pd

def search_movie(query):
    search = tmdb.Search()
    response = search.movie(query=query)
    return search.results[0]["id"]

def xl_to_dict(filename):
    df = pd.read_excel(filename, header=0)
    records_dict = df.to_dict('records')
    return records_dict


if __name__ == "__main__":
    # set up API
    with open("api_key.txt", 'r') as f:
        api_key = f.read()
    
    tmdb.API_KEY = api_key
    tmdb.REQUESTS_TIMEOUT = 5  # seconds, for both connect and read
    tmdb.REQUESTS_SESSION = requests.Session()
    
    # get excel data to read and use for search
    filename = "test/demo_data.xlsx"
    movie_data = xl_to_dict(filename)
    
    # search and retrieve movies
    for movie_dict in movie_data:
        print(f"{movie_dict['Movie Title']} {movie_dict['Year']}")
        movie_id = search_movie(f"{movie_dict['Movie Title']}")
        #print(movie_id)
        movie = tmdb.Movies(movie_id)
        response = movie.info()
        
        movie_dict["Runtime (minutes)"] = movie.runtime
        movie_dict["Budget"] = movie.budget
        movie_dict["IMDB"] = movie.imdb_id
        movie_dict["Country of Origin"] = movie.origin_country[0]

        response = movie.releases()
        for c in movie.countries:
            if c['iso_3166_1'] == 'AU':
                movie_dict["Classification"] = c['certification']
        
        response = movie.credits()
        directors = []  
        for credit in movie.crew:  
            if credit["job"] == "Director":  
                directors.append(credit["name"])
        movie_dict["Director"] = ''.join(directors)
    
    output_df = pd.DataFrame(movie_data)
    output_df.to_excel(f"{filename.replace('/', '/output-')}", index=False) 
