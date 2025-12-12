import pandas as pd
import json
import requests
from tqdm import tqdm
from src.request_movie_site_data import setup_apis, search_tmdb, retrieve_tmdb_data, search_imdb, scrape_rotten_tomatoes, get_letterboxd_user_ratings, get_letterboxd_movie_data

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
    marker_found = False
    # search and retrieve movies
    for movie_dict in tqdm(movie_data):
        movie_fields = movie_dict.keys()
        # if "marker" not in movie_fields and not marker_found:
        #     continue
        # elif "marker" in movie_fields:
        #     marker_found = True
        #     movie_dict.pop("marker")

        # if title or year missing, skip entry entirely
        if ('Movie Title' or 'Year') not in movie_fields:
            error_set.add(f"Error: Entry needs both title and year to attempt data retrieval - {movie_dict})!")
            continue
        
        title = movie_dict['Movie Title']
        year = movie_dict['Year']
        new_data = {}
        tmdb_id = ""
        
        # get TMDB data
        # if ("Director" not in movie_fields) or type(movie_dict['Director']) is float:
        #     # get tmdb info
        #     tmdb_id = search_tmdb(title, year)
        #     if tmdb_id:
        #         movie_dict = retrieve_tmdb_data(movie_dict, tmdb_id)
        #     else:
        #         error_set.add(f"Error: TMDB - No info found for {title} ({year})!")
        
        # get IMDb data
        # if ("IMDb Rating" not in movie_fields) or type(movie_dict['IMDb Rating']) is float:
        #     status_code, response = search_imdb(movie_dict)
        #     if status_code == 200:
        #         new_data["IMDb Rating"] = response["rating"]["aggregateRating"]
        #         try:
        #             new_data["Metascore"] = response["metacritic"]["score"]
        #         except:
        #             pass
        #         new_data["Poster URL"] = response["primaryImage"]["url"]
        #     else:
        #         error_set.add(f"Error: IMDB - No info found for {title} ({year})!")

        if ("Cast (from Letterboxd)" not in movie_fields) or movie_dict['Cast (from Letterboxd)'] is None:
            print(f"{title}: {year} || Letterboxd")
            letterboxd_data = get_letterboxd_movie_data(title, year, letterboxd_user_ratings)
            if not letterboxd_data:
                error_set.add(f"Error: Letterboxd - No info found for {title} ({year})!")
            new_data.update(letterboxd_data)
        
        # get Rotten Tomatoes data
        if ("Tomatometer (Critic Score)" not in movie_fields) or movie_dict['Tomatometer (Critic Score)'] is None:
            print(f"{title}: {year} || Rotten Tomatoes")
            full_cast = movie_dict['Cast (from Letterboxd)'].split(', ') if 'Cast (from Letterboxd)' in movie_fields else []
            rt_data = scrape_rotten_tomatoes(title, year, full_cast)
            if not rt_data:
                error_set.add(f"Error: Rotten Tomatoes - No info found for {title} ({year})!")
            new_data.update(rt_data)
        
        # https://github.com/mattgrosso/film-awards-api
        if ('IMDb ID' in movie_fields) and type(movie_dict['IMDb ID']) is not float and movie_dict['IMDb ID'] is not None:
            if "Academy Award Nominations" not in movie_fields or movie_dict["Academy Award Nominations"] is None or '(' in str(movie_dict["Academy Award Details"]):
                award_url = "https://web-production-b8145.up.railway.app/awards/imdb/" + movie_dict['IMDb ID']
                awards_response = requests.get(award_url)
                if awards_response.status_code == 200:
                    awards_json = awards_response.json()
                    new_data["Academy Award Nominations"] = len(awards_json)
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
                    new_data["Academy Award Wins"] = num_wins
                    new_data["Academy Award Details"] = ':'.join([str(details) for details in nom_list])
                else:
                    new_data["Academy Award Nominations"] = 0
                    new_data["Academy Award Wins"] = 0
                    error_set.add(f"Error: Academy Awards - No info found for {title} ({year})!")

        # add all the details, then ratings, then cast and poster url
        priority_fields = [
            'Director', 'Runtime (minutes)', 'Budget', 'Box Office', 
            'Country of Origin', 'Classification', 'IMDb ID', 'IMDb Rating',
            'Metascore', 'Tomatometer (Critic Score)', 'Popcornmeter (Audience Score)',
            'Letterboxd Average Rating', 'Letterboxd My Rating', 'Academy Award Nominations',
            'Academy Award Wins', 'Academy Award Details'
        ]
        if new_data:
            print(f"\n{title} ({year}): {new_data}")
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