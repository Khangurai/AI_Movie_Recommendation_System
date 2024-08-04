#1. Import Necessary Libraries
import streamlit as st  # Web app framework
import pickle  # Load saved Python objects
import requests  # HTTP requests
from urllib.parse import quote  # Encode URLs
import cohere  # Text generation API
import os  # Interact with the operating system
from dotenv import load_dotenv  # Load environment variables
from deep_translator import GoogleTranslator  # Text translation
import promptToggle  # Custom module for additional functionality

#2. Load Environment Variables
# Load environment variables from the .env file
load_dotenv()

# Get API keys from environment variables
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

#. Load Data Files
# Define the path to the folder containing data files
movieList_path = r'E:\MRS\main\Dataset'
similarity_path = r'E:\MRS\main\Dataset'

# Try to load movie and similarity data from pickle files
try:
    with open(os.path.join(movieList_path, 'movies_listUpdate.pkl'), 'rb') as file:
        movies = pickle.load(file)
    with open(os.path.join(similarity_path, 'similarity_TfidfVectorizer.pkl'), 'rb') as file:
        similarity = pickle.load(file)

    print("Movie list and similarity files loaded successfully!")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except pickle.PickleError as e:
    print(f"Error loading pickle file: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# Extract movie titles for the dropdown menu
movies_list = movies['title'].values

#4. API Configurations
# Try to configure Cohere API
try:
    co = cohere.Client(COHERE_API_KEY)  # Create a Cohere client instance

#5. Helper Functions
#5.1. Fetch Movie URL
    def fetch_movie_url(movie_title):
        cleaned_title = movie_title.replace(' ', '-').replace('&', '').replace(':', '')
        encoded_title = quote(cleaned_title.lower())  # Encode the title for use in URLs
        return f"https://www.channelmyanmar.to/{encoded_title}/"  # Return the movie URL

#5.2. Fetch Movie Poster
    def fetch_poster(movie_id):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url).json()  # Make an HTTP request to get movie details
        poster_path = response.get('poster_path', '')  # Get the poster path
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"  # Return the full poster URL
        return "https://via.placeholder.com/500x750?text=No+Poster+Available"  # Return a placeholder if no poster is available

#5.3. Recommend Similar Movies
    def recommend(selected_movie_title):
        index = movies[movies['title'] == selected_movie_title].index[0]  # Find the index of the selected movie
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])  # Sort similar movies by similarity
        recommend_movie = []
        recommend_poster = []
        movie_urls = []
        for i in distances[0:5]:  # Get top 5 similar movies
            movie_id = movies.iloc[i[0]].id  # Get the movie ID
            movie_title = movies.iloc[i[0]].title  # Get the movie title
            recommend_movie.append(movie_title)
            recommend_poster.append(fetch_poster(movie_id))  # Get the poster for each movie
            movie_urls.append(fetch_movie_url(movie_title))  # Get the URL for each movie
        return recommend_movie, recommend_poster, movie_urls

#5.4. Fetch Popular Movies
    def fetch_popular_movies():
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch popular movies. Status code: {response.status_code}")
            return []
        data = response.json()
        popular_movies = data.get('results', [])  # Get the list of popular movies
        return [(movie['title'], movie['id'], movie.get('poster_path', '')) for movie in popular_movies]  # Return movie details

#5.5. Translate Text While Preserving Titles
    def translate_text_except_titles(text):
        import re

        # Find all titles within curly braces
        titles = re.findall(r'\{(.*?)\}', text)

        # Replace titles with placeholders
        placeholder_text = re.sub(r'\{(.*?)\}', '{}', text)

        # Translate the non-title text
        translated_text = GoogleTranslator(source='auto', target='my').translate(placeholder_text)

        # Reinsert titles into the translated text
        for title in titles:
            translated_text = translated_text.replace('{}', title, 1)

        return translated_text

    def fetch_now_playing():
        url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Failed to fetch now playing movies. Status code: {response.status_code}")
            return []
        data = response.json()
        now_playing_movies = data.get('results', [])
        return [(movie['title'], movie['id'], movie.get('poster_path', '')) for movie in now_playing_movies]

#6. Streamlit UI Setup
    # Set the title of the web app
    st.title("AI Powered Movie Recommendation System")

    # Inject custom CSS to style the movie posters
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        .poster-container {
            display: inline-block;
            position: relative;
            cursor: pointer;
            margin: 10px;
        }

        .poster-container img {
            transition: transform 0.3s ease;
            border-radius: 10px;
        }

        .poster-container img:hover {
            transform: scale(1.1);
        }

        .poster-container .poster-title {
            position: absolute;
            font-family: 'Roboto', sans-serif;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            text-align: center;
            padding: 5px;
            border-top: 0.5px solid #00f1ff;
            border-bottom: 0.5px solid #00f1ff;
            border-radius: 0 0 10px 10px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .poster-container:hover .poster-title {
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

#7. Sidebar and Dropdown Setup
    # Create a sidebar with tabs for Popular and Now Playing movies
    tabs = st.sidebar.tabs(["Popular", "Now Playing"])

    with tabs[0]:  # Popular Movies tab
        st.header('Popular Movies')
        popular_movies = fetch_popular_movies()
        if popular_movies:
            for title, movie_id, poster_path in popular_movies:
                poster_url = "https://image.tmdb.org/t/p/w500/" + poster_path if poster_path else "https://via.placeholder.com/500x750?text=No+Poster+Available"
                movie_url = fetch_movie_url(title)
                st.markdown(
                    f'<div class="poster-container">'
                    f'<a href="{movie_url}" target="_blank">'
                    f'<img src="{poster_url}" width="200" height="250" />'
                    f'</a>'
                    f'<div class="poster-title">{title}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.write("No popular movies available.")

    with tabs[1]:  # Now Playing Movies tab
        st.header('Now Playing')
        now_playing_movies = fetch_now_playing()
        if now_playing_movies:
            for title, movie_id, poster_path in now_playing_movies:
                poster_url = "https://image.tmdb.org/t/p/w500/" + poster_path if poster_path else "https://via.placeholder.com/500x750?text=No+Poster+Available"
                movie_url = fetch_movie_url(title)
                st.markdown(
                    f'<div class="poster-container">'
                    f'<a href="{movie_url}" target="_blank">'
                    f'<img src="{poster_url}" width="200" height="250" />'
                    f'</a>'
                    f'<div class="poster-title">{title}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.write("No movies are currently playing.")

    # Dropdown menu to select a movie from the list
    select_value = st.selectbox('Select Movie', movies_list, key='select_movie')

#8. Generate and Display Recommendations
    # Generate prompt for recommendations
    prompt = (f"You are a movie recommender and your job is to recommend new movies based on user input."
              f"Please recommend three trending movies similar to '{select_value}', including their year of release and a very short description for each.")
    if st.button('Show Recommend', key='show_recommend'):
        # Generate a recommendation response from Cohere
        response = co.generate(
            model='command-xlarge-nightly',  # Use a specific model for text generation
            prompt=prompt,
            max_tokens=200,
            temperature=0.9
        )

        response_text = response.generations[0].text

        # Translate the response text while preserving movie titles
        translated_text = translate_text_except_titles(response_text)
        st.write(translated_text)  # Display the translated text

        # Get recommendations
        movie_names, movie_posters, movie_urls = recommend(select_value)
        columns = st.columns(len(movie_names))  # Create columns dynamically based on the number of movies

        for i, col in enumerate(columns):
            with col:
                col.markdown(
                    f'''
                    <div class="poster-container">
                        <a href="{movie_urls[i]}" target="_blank">
                            <img src="{movie_posters[i]}" style="width: 200px; height: 150px;
                            object-fit: cover;" />
                        </a>
                        <div class="poster-title">{movie_names[i]}</div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

#9. Additional Functionality and Error Handling
    # Call the custom promptToggle functionality
    toggle = promptToggle.main()

except Exception as e:
    st.error(f"An error occurred: {e}")  # Display any errors that occur
