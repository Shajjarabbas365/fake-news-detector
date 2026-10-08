from django.shortcuts import render, redirect
from .models import ScanRecord
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import pickle
import os
import re
import pandas as pd
import requests
from scipy.sparse import hstack
import feedparser
import urllib.parse
import PyPDF2
import docx
from transformers import pipeline
from django.contrib.auth.decorators import login_required

BASE_DIR = settings.BASE_DIR

# ==========================================
# Load Model, Vectorizer and Scaler (legacy TF-IDF model)
# ==========================================
try:
    with open(os.path.join(BASE_DIR, "master_model.pkl"), "rb") as f:
        model = pickle.load(f)

    with open(os.path.join(BASE_DIR, "master_vectorizer.pkl"), "rb") as f:
        vectorizer = pickle.load(f)

    with open(os.path.join(BASE_DIR, "scaler.pkl"), "rb") as f:
        scaler = pickle.load(f)

except Exception as e:
    print("Model Loading Error:", e)
    model, vectorizer, scaler = None, None, None


# ==========================================
# Load Deep Learning Model (Global Level)
# Loaded once outside the view function, so it's kept in
# memory when the server starts instead of reloading it
# on every single request.
# ==========================================
print("Loading Deep Learning Model... (may take a while on first run)")
try:
    # Using 'roberta-fake-news-classification', a model built
    # specifically for this task
    ai_detector = pipeline(
        "text-classification",
        model="hamzab/roberta-fake-news-classification"
    )
    print("Deep Learning Model Successfully Loaded!")
except Exception as e:
    print("Model Loading Error:", e)
    ai_detector = None


# ==========================================
# Function to Extract Structural Features
# (kept for the legacy Random Forest path, if ever used)
# ==========================================
def get_structural_features(text):
    text = str(text)

    exclamation_count = text.count("!")
    question_count = text.count("?")
    caps_count = len([w for w in text.split() if w.isupper() and len(w) > 1])
    word_count = len(text.split())

    return pd.DataFrame(
        [[
            exclamation_count,
            question_count,
            caps_count,
            word_count
        ]],
        columns=[
            "exclamation_count",
            "question_count",
            "caps_count",
            "word_count"
        ]
    )

def home(request):  # public page: no login needed to check news
    context = {}

    if request.method == "POST":

        # ==========================================
        # PART 0: GET TEXT (TYPED OR UPLOADED FILE)
        # ==========================================

        # Text from the textarea
        news_text = request.POST.get("news_text", "").strip()

        # Check if the user uploaded a file instead
        uploaded_file = request.FILES.get("news_document")

        if uploaded_file:
            print(f"File uploaded by user: {uploaded_file.name}")
            file_name = uploaded_file.name.lower()

            try:
                # Plain text file
                if file_name.endswith(".txt"):
                    news_text = uploaded_file.read().decode("utf-8")

                # PDF file
                elif file_name.endswith(".pdf"):
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = []
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text.append(text)
                    news_text = " ".join(extracted_text)

                # Word document
                elif file_name.endswith(".docx"):
                    doc = docx.Document(uploaded_file)
                    news_text = " ".join(
                        [para.text for para in doc.paragraphs]
                    )

                else:
                    print(f"Unsupported file type: {file_name}")
                    context["result"] = "Unsupported file type"
                    context["confidence"] = 0
                    context["color"] = "red"
                    context["trusted_links"] = []
                    context["general_links"] = []
                    news_text = ""

            except Exception as e:
                print(f"Error reading file: {e}")
                context["result"] = "Error reading file"
                context["confidence"] = 0
                context["color"] = "red"
                context["trusted_links"] = []
                context["general_links"] = []
                news_text = ""

        context["news_text"] = news_text

        # ==========================================
        # Proceed only if we ended up with some text
        # (either typed directly or extracted from file)
        # ==========================================
        if news_text:

            try:

                # ==========================================
                # PART 1: DEEP LEARNING (RoBERTa) PREDICTION
                # ==========================================
                if ai_detector:
                    # Transformer models can only read up to about
                    # 512 tokens at a time, so we send roughly the
                    # first 2000 characters of the text to the model
                    short_text = news_text[:2000]

                    # One line does the whole prediction! (returns a
                    # dictionary, e.g. {'label': 'FAKE', 'score': 0.98})
                    result_data = ai_detector(short_text)[0]

                    ai_label = result_data["label"].upper()
                    conf_percent = round(result_data["score"] * 100, 2)

                    # Check RoBERTa's label
                    if ai_label == "FAKE":
                        context["result"] = "FAKE NEWS"
                        context["color"] = "red"
                    else:
                        context["result"] = "REAL NEWS"
                        context["color"] = "green"

                    context["confidence"] = conf_percent
                    # Save the scan to history only for logged-in users
                    if request.user.is_authenticated:
                        ScanRecord.objects.create(
                            user=request.user,
                            scanned_text=short_text,  # The text that was scanned
                            result_label=context["result"],  # FAKE NEWS or REAL NEWS
                            confidence_score=conf_percent
                        )
                else:
                    context["result"] = "Model Failed to Load!"
                    context["color"] = "orange"
                    context["confidence"] = 0

                # Build the smart search query once, used by both
                # Part 2 (Wikipedia) and Part 3 (Google News RSS)
                clean_text = re.sub(r"[^\w\s]", "", news_text)
                words = clean_text.split()

                # Find important capitalized words
                important_keywords = [
                    word for word in words
                    if word[0].isupper() and len(word) > 2
                ]

                # If not enough capitalized words, use long words
                if len(important_keywords) < 2:
                    important_keywords = [
                        word for word in words
                        if len(word) > 4
                    ]

                # Create smart search query
                if len(important_keywords) >= 2:
                    search_query = " ".join(important_keywords[:4])
                else:
                    search_query = " ".join(words[:4])

                # ==========================================
                # PART 2: WIKIPEDIA API (SMART SEARCH)
                # ==========================================

                trusted_links = []

                try:

                    print(f"\nAI Smart Heading: '{search_query}'")

                    headers = {
                        "User-Agent": (
                            "TruthLensBot/1.0 "
                            "(Educational Project; contact@example.com)"
                        )
                    }

                    wiki_url = (
                        "https://en.wikipedia.org/w/api.php"
                        f"?action=query"
                        f"&list=search"
                        f"&srsearch={search_query}"
                        f"&utf8="
                        f"&format=json"
                    )

                    response = requests.get(
                        wiki_url,
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 200:

                        data = response.json()

                        search_results = (
                            data.get("query", {})
                                .get("search", [])
                        )

                        if len(search_results) > 0:

                            for item in search_results[:3]:
                                trusted_links.append({
                                    "title": f"Wikipedia Entity: {item['title']}",
                                    "link": f"https://en.wikipedia.org/?curid={item['pageid']}"
                                })

                            print(
                                f"Found {len(trusted_links)} Wikipedia links!"
                            )

                        else:
                            print(
                                "No matching Wikipedia results found."
                            )

                    else:
                        print(
                            f"Wikipedia Server Error: {response.status_code}"
                        )

                except Exception as e:
                    print("Wikipedia API Error:", e)

                # Send Wikipedia results to context
                context["trusted_links"] = trusted_links

                # ==========================================
                # PART 3: GENERAL WEB MENTIONS (Free RSS Feeds)
                # ==========================================
                general_links = []

                try:
                    print(f"\nSearching Live News (RSS) for: '{search_query}'")

                    # Make the query URL-safe (spaces -> %20 etc.)
                    encoded_query = urllib.parse.quote(search_query)

                    # Google News RSS Search (free, no limits, covers
                    # major outlets like CNN, BBC, Reuters, etc.)
                    rss_url = (
                        "https://news.google.com/rss/search"
                        f"?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
                    )

                    # Parse the RSS feed
                    feed = feedparser.parse(rss_url)

                    if len(feed.entries) > 0:
                        # Grab the top 3 latest matching articles
                        for entry in feed.entries[:3]:
                            # RSS entries already include the source name
                            # in the title, so no extra cleanup needed
                            general_links.append({
                                "title": entry.title,
                                "link": entry.link
                            })
                        print(
                            f"Found {len(general_links)} recent articles from RSS feed!"
                        )
                    else:
                        print("No recent articles found in RSS feed for this topic.")

                except Exception as e:
                    print("RSS Feed Error:", e)

                # Send RSS results to context as well
                context["general_links"] = general_links

            except Exception as e:

                context["result"] = f"System Error: {str(e)}"
                context["color"] = "red"
                context["confidence"] = 0
                context["trusted_links"] = []
                context["general_links"] = []

    return render(request, "index.html", context)


# ==========================================
# User Signup / Registration View
# ==========================================
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log the user in after successful registration
            return redirect('/')  # Redirect the user to the home page
    else:
        form = UserCreationForm()
    
    return render(request, 'signup.html', {'form': form})
# Add this at the end of views.py

@login_required
def history(request):
    # Retrieve only the logged-in user's scan history,
    # with the most recent scans displayed first (-created_at)
    user_scans = ScanRecord.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'history.html', {'scans': user_scans})