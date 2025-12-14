# The Movie Database Automation

## Installation

Navigate to the folder where you want the program saved, start a command line by typing 'cmd' + Enter into the File Explorer address bar:

<img src="assets/type_cmd.jpg" alt="Type 'cmd' to open command prompt" width="300" height="200">

In the command line, paste the below command:
```
git clone https://github.com/amberave/tmdb.git;cd tmdb;python -m venv venv\;venv\Scripts\activate;pip install -r requirements.txt
```
1. Login to [The Movie Database](https://www.themoviedb.org/settings/api).
2. Scroll to the bottom of the [API page](https://www.themoviedb.org/settings/api) and copy your API Key.
3. Create a file called `api_key.txt` in this folder (`tmdb`) and paste your API key into it. 

## Usage

### Source Data
Ensure you have placed an Excel file in the `input` folder. The program will try and load `movies_database.xlsx`. If your file is not named this, you can rename it to `movies_database.xlsx` or change the value `filename` in `[main.py](main.py)`.

### Running Programs
Open the folder which contains `get_movie_info.py`.

Start a command line by typing 'cmd' + Enter into the File Explorer address bar:

<img src="assets/type_cmd.jpg" alt="Type 'cmd' to open command prompt" width="300" height="200">

In the command line, paste the below command:
```
venv\Scripts\activate;python ./get_movie_info.py
```
You will be asked to input a character:

| Input | Meaning |
|--|--|
| 'u' | **Update** - continue from where program last left off |
| 's' | **Start** - program will restart from the very beginning, discarding any existing data.|

You will be asked to input another character:

| Input | Meaning |
|--|--|
| 'c' | Run the program over all values and attempt to fill any blank fields |
| Enter (nothing) | Skip all filled-in rows and only fill most recently added rows (with no program-generated data). |

For subsequent calls of this command, press the up arrow then Enter.

### Output Data

The output data will be saved to the `output` folder under the name `output-[filename].xlsx` where 'filename' is the original filename. There will also be an errors log named `output-[filename]_errors.txt` which will show the title and year along with the site where data retrieval failed. 

## Data Details:

| Field | Details (if needed) |
|-------|---------|
| **Fields from TMDB** ||
| Director| If a list, comma-space separated (', ')|
| Runtime (minutes)| In minutes |
| Budget| Revenue internationally in US dollars (I think) |
| Box Office| In US dollars (I think) |
| Country of Origin| If a list, comma-space separated (', ')|
| Classification| Australian classification. If Aus classification unavailable, US classification will be added with '(US)' after. (e.g. Aus classification: 'G', US classification: 'G (US)')|
|IMDb ID| This is used in other database searches, primarily Academy Award data|
| **Fields from IMDb** | |
| IMDb Rating| |
| Metascore| If page exists but no score is given, value is "Not Listed". If no page exists, value is blank.|
| Poster URL| URL to a good quality poster.|
| **Fields from Letterboxd** ||
| Letterboxd My Rating| This is your Letterboxd rating. If you have logged the film on Letterboxd, value is "Not Rated", if you have not interacted with it on Letterboxd, value is blank. *Note: if you watch a film marked "Not Rated", this program will not update that field. Either remove "Not Rated" (and program will pull rating from Letterboxd) or manually put your rating into field.*|
| Letterboxd Average Rating| Average Letterboxd rating retrieved from Letterboxd to 2 decimal places (e.g. 4.35). Not sure exactly how they calculate it on Letterboxd, there is no consistent rounding |
| Letterboxd Review Count| *Number* |
| Letterboxd Rating Count| *Number* |
| Cast (from Letterboxd)| Values are comma-space separated (', ')|
| Spoken Languages| If multiple, values are comma-space separated (', ') |
| Runtime (from Letterboxd)| In minutes. TV shows (e.g. Mini Series) do not have runtime data on TMDB but do have data on Letterboxd. This should supplement any missing data in column 'Runtime (minutes)'.
| TMDB ID (from Letterboxd)| Can be used to get TMDB data directly if there are any issues searching. |
| IMDb ID (from Letterboxd)| Backup for 'IMDb ID' column if TMDB search did not retrieve IMDb ID |
| Letterboxd Slug | Letterboxd searches using this. This is also used to pull latest data from Letterboxd; if a slug is not already in the data (you've just watched it), program adds it. (e.g. Slug for V for Vendetta is 'v-for-vendetta')|
| **Fields from Rotten Tomatoes** | Films are retrieved based on logic: year matches (with 1 year difference allowance) AND (title is exact match OR top 3 cast from RT search are all in Letterboxd cast list). This means if title is not exact match (or has non alphanumeric characters) and a top-billed cast member has a different name (e.g. Christopher Sanders vs Chris Sanders) then result will not be retrieved.
| Tomatometer (Critic Score)| Out of 100. If page exists but no score is given, value is "Not Listed". If no page exists, value is blank. |
| Popcornmeter (Audience Score)| Out of 100. If page exists but no score is given, value is "Not Listed". If no page exists, value is blank.|
| **Fields from Academy Awards Database** ||
| Academy Award Nominations| *Number* |
| Academy Award Wins| *Number*|
| Academy Award Details | Split by : (colon) -> ; (semicolon) -> , (comma)<br>Entries are colon separated (':'). Values in each entry (Category; Nominee/s; Winner/Nominee) are semicolon-space separated ('; '). If there are multiple nominees, their names are comma-space separated (', '). (e.g. 'Best Animated Short; Nick Park; Winner:Best Picture; Producer1, Producer2, Producer3; Nominee') |

## Troubleshooting

For any troubleshooting: THINK.

Then contact me if unsuccessful 😊