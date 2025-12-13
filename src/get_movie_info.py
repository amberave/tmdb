import pandas as pd
import json
import requests
from tqdm import tqdm
from src.request_movie_site_data import setup_apis, search_tmdb, retrieve_tmdb_data, search_imdb, scrape_rotten_tomatoes, get_letterboxd_user_ratings, get_letterboxd_movie_data, get_oscars_data

def load_movie_data(filename):
    input_filename = "input/" + filename
    while True:
        mode = input("Do you want to update or start from beginning? Enter 'u' or 's': ")
        if mode.lower() == 'u':
            # open save file in tmp folder
            try:
                save_filename = "src/tmp/" + filename.replace(".xlsx", "_save_file.json")
                with open(save_filename, 'r') as file:
                    movie_data = json.load(file)
            except FileNotFoundError:
                raise FileNotFoundError(f"Error: There is no save file for '{filename}'. Check the filename and rerun the program if save file exists, else select 's' to start from beginning and filename will be generated.")
            break
        elif mode.lower() == 's':
            # get excel data to read and use for search
            try:
                df = pd.read_excel(input_filename, header=0)
                df = df.replace({float('nan'): None})
                movie_data = df.to_dict('records')
                
                # if starting new, clear errors log
                open('src/tmp/' + filename.replace(".xlsx", "_errors.txt"), 'w').close()
            except FileNotFoundError:
                raise FileNotFoundError(f"Error: There is no file in 'input' folder called '{filename}'.\nCheck the filename and rerun the program.")
            break
    return movie_data

def save_progress(filename, error_save_folder, movie_data, error_set):
    save_filename = "src/tmp/" + filename.replace(".xlsx", "_save_file.json")
    err_filename = "src/tmp/" + filename.replace(".xlsx", "_errors.txt")
    # save all entries
    with open(save_filename, "w") as f:
        json.dump(movie_data, f)
    
    # get errors and only save unique values
    with open(err_filename, 'r') as f:
        err_file_text = f.read()
        err_file_list = set(err_file_text.split('\n'))
    error_set.update(err_file_list)
    error_list = sorted([v for v in error_set if type(v) is str])
    with open(error_save_folder + filename.replace(".xlsx", "_errors.txt"), 'w') as f:
        errors = '\n'.join(error_list)
        if '\u2044' in errors:
            errors = errors.replace('\u2044', '')
        f.write(errors)



def get_movie_info(filename):
    tmdb = setup_apis()
    movie_data = load_movie_data(filename)
    letterboxd_user_ratings = get_letterboxd_user_ratings("DWynter10")
    error_set = set()
    
    i = 0
    # search and retrieve movies
    for movie_dict in tqdm(movie_data):
        movie_fields = movie_dict.keys()
        
        def field_exists_and_valid(fieldname):
            return fieldname in movie_fields and movie_dict[fieldname] is not None
        
        def is_missing_info(fields:list):
            any_none_fields = any(movie_dict.get(key) is None for key in fields if key in movie_dict)
            missing_fields = not all(key in movie_fields for key in fields)
            return missing_fields or any_none_fields

        # if title or year missing, skip entry entirely
        if is_missing_info(['Movie Title', 'Year']):
            error_set.add(f"Error: Entry needs both title and year to attempt data retrieval - {movie_dict})!")
            continue
        
        title = movie_dict['Movie Title']
        year = movie_dict['Year']
        new_data = {}
        tmdb_id = ""
        
        site_fields = [
            'Director', 'Runtime (minutes)', 'Budget', 'Box Office', 'Country of Origin', 
            'Spoken Languages', 'Classification', 'IMDb ID'
        ]
        #print(f"{title} ({year}): Missing fields from IMDb {is_missing_info(site_fields)}")
        # get TMDB data
        if is_missing_info(site_fields):
            medium = movie_dict['Medium'] if field_exists_and_valid('Medium') else None
            # get TMDB ID
            if ("TMDB ID" not in movie_fields or movie_dict['TMDB ID'] is None):
                tmdb_id = search_tmdb(title, year, medium)
            else:
                tmdb_id = movie_dict['TMDB ID']
            # retrieve data from TMDB
            if tmdb_id:
                movie_dict = retrieve_tmdb_data(movie_dict, tmdb_id, medium)
            else:
                error_set.add(f"Error: TMDB - No info found for {title} ({year})!")
        
        # get IMDb data
        site_fields = ['IMDb Rating', 'Metascore', 'Poster URL']
        if is_missing_info(site_fields):
            imdb_data = search_imdb(movie_dict)
            if not imdb_data:
                error_set.add(f"Error: IMDB - No info found for {title} ({year})!")
            else:
                new_data.update(imdb_data)


        # get IMDb data
        site_fields = [
            'Letterboxd Average Rating', 'Letterboxd My Rating', 'Letterboxd Review Count', 
            'Letterboxd Rating Count', 'Cast (from Letterboxd)', 'Runtime (from Letterboxd)', 
            'TMDB ID (from Letterboxd)', 'IMDb ID (from Letterboxd)'
        ]
        if is_missing_info(site_fields):
            letterboxd_data = get_letterboxd_movie_data(title, year, letterboxd_user_ratings)
            if not letterboxd_data:
                error_set.add(f"Error: Letterboxd - No info found for {title} ({year})!")
            new_data.update(letterboxd_data)
        
        # get Rotten Tomatoes data
        site_fields = ['Tomatometer (Critic Score)', 'Popcornmeter (Audience Score)']
        if is_missing_info(site_fields):
            full_cast = movie_dict['Cast (from Letterboxd)'].split(', ') if 'Cast (from Letterboxd)' in movie_fields and movie_dict['Cast (from Letterboxd)'] is not None else []
            rt_data = scrape_rotten_tomatoes(title, year, movie_dict['Medium'], full_cast)
            if not rt_data:
                error_set.add(f"Error: Rotten Tomatoes - No info found for {title} ({year})!")
            new_data.update(rt_data)
        
        # https://github.com/mattgrosso/film-awards-api
        imdb_id = movie_dict['IMDb ID'] if field_exists_and_valid('IMDb ID') else movie_dict['IMDb ID (from Letterboxd)'] if field_exists_and_valid('IMDb ID (from Letterboxd)') else None
        if imdb_id is not None:
            site_fields = ["Academy Award Nominations", 'Academy Award Wins', 'Academy Award Details']
            if is_missing_info(site_fields):
                oscars_data = get_oscars_data(imdb_id)
                if not oscars_data:
                    new_data["Academy Award Nominations"] = 0
                    new_data["Academy Award Wins"] = 0
                    error_set.add(f"Error: Academy Awards - No info found for {title} ({year})!")

        # add all the details, then ratings, then cast and poster url
        priority_fields = [
            'Director', 'Runtime (minutes)', 'Budget', 'Box Office', 
            'Country of Origin', 'Spoken Languages', 'Classification', 'IMDb ID', 'IMDb Rating',
            'Metascore', 'Tomatometer (Critic Score)', 'Popcornmeter (Audience Score)',
            'Letterboxd Average Rating', 'Letterboxd My Rating', 'Academy Award Nominations',
            'Academy Award Wins', 'Academy Award Details'
        ]
        if new_data:
            i += 1
        
        for k in list(new_data.keys()):
            if k in priority_fields:
                movie_dict[k] = new_data.pop(k)
        movie_dict.update(new_data)

        # save function
        if i == 6:
            save_progress(filename, "src/tmp/", movie_data, error_set)
            i = 0

    save_progress(filename, "output/output-", movie_data, error_set)
    output_df = pd.DataFrame(movie_data)
    
    output_filename = "output/output-" + filename
    output_df.to_excel(output_filename, index=False)
    
    print(f"All data saved to '{output_filename}'\nErrors saved to 'output/output-{filename.replace('.xlsx', '_errors.txt')}")