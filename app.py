import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import re
import requests
from bs4 import BeautifulSoup

st.title("📚 Book Scraper - Books to Scrape")
st.markdown("This app scrapes book information from [Books to Scrape](http://books.toscrape.com)")

@st.cache_data(show_spinner=True)
def scrape_books():
    titles, prices, availabilities, ratings, categories = [], [], [], [], []
    for page in range(1, 6):
        url = f"http://books.toscrape.com/catalogue/page-{page}.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        books = soup.find_all("article", class_="product_pod")

        for book in books:
            title = book.h3.a["title"]
            price = book.find("p", class_="price_color").text
            availability = book.find("p", class_="instock availability").text.strip()
            rating = book.p["class"][1]
            book_relative_url = book.h3.a["href"]
            book_url = "http://books.toscrape.com/catalogue/" + book_relative_url.replace('../../../', '')
            book_response = requests.get(book_url)
            book_soup = BeautifulSoup(book_response.content, "html.parser")
            category = book_soup.find("ul", class_="breadcrumb").find_all("li")[2].text.strip()

            titles.append(title)
            prices.append(float(price[1:]))
            availabilities.append(availability)
            ratings.append(rating)
            categories.append(category)

    return pd.DataFrame({
        "Title": titles,
        "Price": prices,
        "Availability": availabilities,
        "Rating": ratings,
        "Category": categories
    })

# Load data and apply rating map
@st.cache_data
def load_data():
    df = scrape_books()
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    df['Rating'] = df['Rating'].map(rating_map)
    return df

# Get data
data = load_data()

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
categories = st.sidebar.multiselect("Category:", sorted(data["Category"].unique()), default=sorted(data["Category"].unique()))
min_price, max_price = st.sidebar.slider("Price Range (£):", float(data["Price"].min()), float(data["Price"].max()), (float(data["Price"].min()), float(data["Price"].max())))
ratings = st.sidebar.multiselect("Rating:", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])

# Filtered Data
filtered_data = data[
    (data["Category"].isin(categories)) &
    (data["Price"] >= min_price) & (data["Price"] <= max_price) &
    (data["Rating"].isin(ratings))
]

# Show Data
st.subheader("📊 Dataset Table")
st.dataframe(filtered_data)

# Summary
st.markdown("### 📌 Dataset Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Unique Titles", filtered_data["Title"].nunique())
col2.metric("Categories", filtered_data["Category"].nunique())
col3.metric("Avg. Price (£)", f"{filtered_data['Price'].mean():.2f}")
col4.metric("Avg. Rating", f"{filtered_data['Rating'].mean():.2f}")

# Visualizations
with st.expander("📊 Rating of Books"):
    fig, ax = plt.subplots(figsize=(10, min(30, 0.3 * len(filtered_data))))
    sns.barplot(x="Rating", y="Title", data=filtered_data.sort_values("Rating"), ax=ax, palette="colorblind")
    st.pyplot(fig)

with st.expander("📊 Price of Books"):
    fig, ax = plt.subplots(figsize=(10, min(30, 0.3 * len(filtered_data))))
    sns.barplot(x="Price", y="Title", data=filtered_data.sort_values("Price"), ax=ax, palette="bright")
    st.pyplot(fig)

with st.expander("📊 Books per Category"):
    fig, ax = plt.subplots(figsize=(20, 6))
    sns.countplot(x="Category", data=filtered_data, palette="dark", order=filtered_data["Category"].value_counts().index)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig)
with st.expander("📊 Price by Category (Boxplot)"):
    fig, ax = plt.subplots(figsize=(20, 8))
    sns.boxplot(x="Category", y="Price", data=filtered_data, palette="deep")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    st.pyplot(fig)

with st.expander("📊 Rating Heatmap per Category"):
    heatmap_data = filtered_data.pivot_table(index="Category", columns="Rating", aggfunc="size", fill_value=0)
    fig, ax = plt.subplots(figsize=(15, 8))
    sns.heatmap(heatmap_data, cmap="coolwarm", annot=True, ax=ax)
    st.pyplot(fig)

with st.expander("📊 Availability Distribution"):
    availability_counts = filtered_data["Availability"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(availability_counts, labels=availability_counts.index, autopct='%1.1f%%', startangle=90, shadow=True, colors=sns.color_palette("Set3"))
    ax.axis('equal')
    st.pyplot(fig)

with st.expander("📊 Rating Distribution"):
    rating_counts = filtered_data["Rating"].value_counts().sort_index()
    explode = [0] * len(rating_counts)
    if 5 in rating_counts.index:
        explode[rating_counts.index.get_loc(5)] = 0.1
    fig, ax = plt.subplots()
    ax.pie(rating_counts, labels=rating_counts.index, autopct='%1.1f%%', startangle=90, explode=explode, shadow=True, colors=sns.color_palette("Set1"))
    ax.axis('equal')
    st.pyplot(fig)