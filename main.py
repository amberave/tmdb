from src.get_movie_info import get_movie_info

if __name__ == "__main__":
    filename = "movies_database.xlsx"
    letterboxd_username = "DWynter10"
    get_movie_info(filename, letterboxd_username)
