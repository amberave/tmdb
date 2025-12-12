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

Open the folder which contains `get_movie_info.py`.

Start a command line by typing 'cmd' into the File Explorer address bar:

![Type cmd](assets/type_cmd.jpg)

In the command line, paste the below command:
```
python ./get_movie_info.py
```
Enter 'u' for **update** - continue from where program last left off - or enter 's' for **start** - program will restart from the very beginning, discarding any existing data. 

For subsequent calls of this command, press the up arrow then Enter.

## Setting up environment

```
python -m venv venv\;venv/Scripts/activate;pip install -r requirements.txt
```

## Troubleshooting

For any troubleshooting: THINK.

Then contact me if unsuccessful 😊