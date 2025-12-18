from src.get_movie_info import get_movie_info, load_movie_data

if __name__ == "__main__":
    filename = "movies_database.xlsx"
    letterboxd_username = "jigsaw4real"
    movie_data = load_movie_data(filename)
    skip_checked_entries_input = input("Input 'c' to check all entries for missing data, else press Enter to skip to newly added rows: ")
    skip_checked_entries = False if skip_checked_entries_input == 'c' else True
    get_movie_info(filename, letterboxd_username, movie_data, skip_checked_entries)
