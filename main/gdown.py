import gdown
import streamlit as st
import pickle

# Google Drive shareable link
url = 'https://drive.google.com/file/d/1cC1AP0qXIQmOQ8iNiGj9DTE0WFXhw1E9/view?usp=drive_link'

# Local file name where the file will be saved
output = 'similarity_TfidfVectorizer.pkl'
output2 = 'movie_lists.pkl'


# Download the file
gdown.download(url, output, quiet=False)

# Load the pickle file
with open(output, 'rb') as file:
    data = pickle.load(file)

# Now you can use 'data' in your app
st.write(data)
