from src.get_movie_info import get_movie_info

if __name__ == "__main__":
    filename = "movies_database.xlsx"
    # f = input(f"Program will retrieve and search based on data in '{filename}'.\nPress Enter to use this data. To use other data, type the filename here (include .xlsx): ")
    # if f:
    #     filename = f
    get_movie_info(filename)
