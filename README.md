# The Movie Database Automation

## Installation

1. Download and install [Python](https://www.python.org/downloads/)
2. Open a terminal (consecutively: Windows key + 'wt' + Enter)
3. Paste the below, this will install all the Python packages you will need:
```
python -m ensurepip --upgrade; pip install pillow; pip install tmdbsimple; pip install requests; pip install pandas; pip install openpyxl
```
4. Login to [The Movie Database](https://www.themoviedb.org/settings/api).
5. Scroll to the bottom of the API page and copy your API Key.
6. Create a file called `api_key.txt` in this folder and paste your API key into it. 

## Running Script

Run the script by opening your terminal in the same folder as `get_movie_info.py` and pasting the below command:
```
python ./get_movie_info.py
```

For subsequent calls of this command, press the up arrow then Enter.

## Troubleshooting

For any troubleshooting: THINK.

Then contact me if unsuccessful 😊