import pandas as pd
import json
import requests
import math
import os
from tqdm import tqdm
from request_movie_site_data import setup_apis, search_tmdb, retrieve_tmdb_data, search_imdb, scrape_rotten_tomatoes, get_letterboxd_user_ratings, get_letterboxd_movie_data, get_oscars_data

def load_movie_data(start_mode=False, filepath=None):
    filename = ''
    if not start_mode:
        with open('src/last_filename.txt', 'r') as f:
            filename = f.read()
        # open save file in tmp folder
        try:
            save_filename = "src/tmp/" + filename.replace(".xlsx", "_save_file.json")
            with open(save_filename, 'r', encoding='utf-8') as file:
                movie_data = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: There is no save file for '{filename}'. Check the filename and rerun the program if save file exists, else select 's' to start from beginning and filename will be generated.")
    else: # if 'update' mode - pull from save file
        filename = os.path.basename(filepath)
        with open('src/last_filename.txt', 'w') as f:
            f.write(filename)
        # get excel data to read and use for search
        try:
            df = pd.read_excel(filepath, header=0)
            df = df.replace({float('nan'): None})
            movie_data = df.to_dict('records')
            
            # if starting new, clear errors log
            open('src/tmp/' + filename.replace(".xlsx", "_errors.txt"), 'w').close()
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: Cannot find file '{filepath}'.")
    return movie_data, filename

def save_progress(filename, error_save_folder, movie_data, error_set):
    save_filename = "src/tmp/" + filename.replace(".xlsx", "_save_file.json")
    err_filename = "src/tmp/" + filename.replace(".xlsx", "_errors.txt")
    # save all entries
    with open(save_filename, "w") as f:
        json.dump(movie_data, f)
    
    # get errors and only save unique values
    with open(err_filename, 'r', encoding='utf-8') as f:
        err_file_text = f.read()
        err_file_list = set(err_file_text.split('\n'))
    error_set.update(err_file_list)
    error_list = sorted([v for v in error_set if type(v) is str])
    with open(error_save_folder + filename.replace(".xlsx", "_errors.txt"), 'w', encoding='utf-8') as f:
        errors = '\n'.join(error_list)
        f.write(errors)

def add_new_letterboxd_entries(movie_data, letterboxd_user_ratings):
    print("\nLoading in your missing logged movies from Letterboxd...")
    available_slugs = [entry["Letterboxd Slug"] for entry in movie_data if 'Letterboxd Slug' in entry]
    missing_films = {slug: v for slug,v in letterboxd_user_ratings["movies"].items() if slug not in available_slugs}
    for film in missing_films:
        entry = {}
        entry["Movie Title"] = missing_films[film]["name"]
        entry["Year"] = missing_films[film]["year"]
        entry["Letterboxd My Rating"] = missing_films[film]["rating"]/2 if missing_films[film]["rating"] is not None else None
        entry["Letterboxd Slug"] = film
        entry["Franchise"] = None
        entry["Medium"] = None
        entry["Logged on Letterboxd"] = "Yes"
        entry["Decade"] = str(math.floor(entry["Year"] / 10) * 10) + 's'
        movie_data.append(entry)
    print(f"You've watched {len(missing_films)} new properties since last upload: {', '.join([v['name'] for v in missing_films.values()])}\n")
    return movie_data, missing_films

def get_movie_info(filename, letterboxd_user_ratings, movie_dict, error_set, skip_checked_entries=True):
        
    def field_exists_and_valid(fieldname):
        return fieldname in movie_dict and movie_dict[fieldname] is not None
    
    def is_missing_info(fields:list):
        any_none_fields = any(movie_dict.get(key) is None for key in fields if key in movie_dict)
        missing_fields = not all(key in movie_dict for key in fields)
        return missing_fields or any_none_fields

    # if title or year missing, skip entry entirely
    if is_missing_info(['Movie Title', 'Year']):
        error_set.add(f"Error: Entry needs both title and year to attempt data retrieval - {movie_dict})!")
        return {}, error_set
    
    title = movie_dict['Movie Title']
    year = movie_dict['Year']
    medium = movie_dict['Medium'] if field_exists_and_valid('Medium') else None
    new_data = {}
    tmdb_id = ""
    
    # Letterboxd is most reliable site for getting info, best one to skip on
    # runtime is not pulled for new entries from Letterboxd, so will pick up those too
    if not is_missing_info(['Runtime (from Letterboxd)']) and skip_checked_entries:
        return {}, error_set
    
    site_fields = [
        'Director', 'Runtime (minutes)', 'Budget', 'Box Office', 'Country of Origin', 
        'Spoken Languages', 'Classification', 'IMDb ID'
    ]
    # get TMDB data
    if is_missing_info(site_fields):
        # get TMDB ID
        if field_exists_and_valid('TMDB ID (from Letterboxd)'):
            tmdb_id = movie_dict['TMDB ID (from Letterboxd)']
        else:
            tmdb_id = search_tmdb(title, year, medium)
        # retrieve data from TMDB
        if tmdb_id:
            tmdb_data = retrieve_tmdb_data(movie_dict, tmdb_id, medium)
            movie_dict.update(tmdb_data)
            new_data.update(tmdb_data)
        else:
            error_set.add(f"Error: TMDB - No info found for {title} ({year})!")

    # get Letterboxd data
    site_fields = [
        'Letterboxd Average Rating', 'Letterboxd My Rating', 'Letterboxd Review Count', 
        'Letterboxd Rating Count', 'Cast (from Letterboxd)', 'Runtime (from Letterboxd)', 
        'TMDB ID (from Letterboxd)', 'IMDb ID (from Letterboxd)', 'Letterboxd Slug'
    ]
    if is_missing_info(site_fields):
        slug = movie_dict["Letterboxd Slug"] if 'Letterboxd Slug' in movie_dict else None
        letterboxd_data = get_letterboxd_movie_data(title, year, letterboxd_user_ratings, slug)
        if not letterboxd_data:
            error_set.add(f"Error: Letterboxd - No info found for {title} ({year})!")
        new_data.update(letterboxd_data)
    
    # get IMDb data
    site_fields = ['IMDb Rating', 'Metascore', 'Poster URL']
    if is_missing_info(site_fields):
        imdb_data = search_imdb(movie_dict)
        if not imdb_data:
            error_set.add(f"Error: IMDB - No info found for {title} ({year})!")
        else:
            movie_dict.update(imdb_data)
    
    # get Rotten Tomatoes data
    site_fields = ['Tomatometer (Critic Score)', 'Popcornmeter (Audience Score)']
    if is_missing_info(site_fields):
        full_cast = movie_dict['Cast (from Letterboxd)'].split(', ') if 'Cast (from Letterboxd)' in movie_dict and movie_dict['Cast (from Letterboxd)'] is not None else []
        rt_data = scrape_rotten_tomatoes(title, year, movie_dict['Medium'], full_cast)
        if not rt_data:
            error_set.add(f"Error: Rotten Tomatoes - No info found for {title} ({year})!")
        new_data.update(rt_data)
    
    # Get Awards data
    # https://github.com/mattgrosso/film-awards-api
    imdb_id = movie_dict['IMDb ID'] if field_exists_and_valid('IMDb ID') else movie_dict['IMDb ID (from Letterboxd)'] if field_exists_and_valid('IMDb ID (from Letterboxd)') else None
    if imdb_id is not None:
        site_fields = ["Academy Award Nominations", 'Academy Award Wins', 'Academy Award Details']
        if is_missing_info(site_fields):
            oscars_data = get_oscars_data(imdb_id, year)
            if not oscars_data:
                error_set.add(f"Error: Academy Awards - No info found for {title} ({year})!")
            else:
                new_data.update(oscars_data)

    return new_data, error_set
    