from flask import Flask, jsonify, render_template_string
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
DB_NAME = "database.db"

# -----------------------
# Designer items with placeholder images
# -----------------------
DESIGNER_ITEMS = [
    ("Gucci", "GG Marmont Bag", "Bags", 1980, "https://picsum.photos/200/200?text=Gucci+Bag"),
    ("Gucci", "Ace Sneakers", "Shoes", 720, "https://picsum.photos/200/200?text=Gucci+Ace"),
    ("Gucci", "Horsebit Loafers", "Shoes", 890, "https://picsum.photos/200/200?text=Gucci+Loafers"),
    ("Prada", "Re-Edition 2000", "Bags", 1250, "https://picsum.photos/200/200?text=Prada+Bag"),
    ("Prada", "Monolith Boots", "Shoes", 1550, "https://picsum.photos/200/200?text=Prada+Boots"),
    ("Balenciaga", "Triple S Sneakers", "Shoes", 1090, "https://picsum.photos/200/200?text=Balenciaga"),
    ("Louis Vuitton", "Neverfull MM", "Bags", 2030, "https://picsum.photos/200/200?text=LV+Bag"),
    ("Dior", "Saddle Bag", "Bags", 3800, "https://picsum.photos/200/200?text=Dior+Bag"),
    ("Off-White", "Industrial Belt", "Accessories", 320, "https://picsum.photos/200/200?text=Off-White+Belt"),
]

# -----------------------
# Database setup
# -----------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            name TEXT,
            category TEXT,
            price REAL,
            image_url TEXT,
            popularity INTEGER,
            last_updated TEXT
        )
    """)
    conn.commit()
    conn.close()

def update_items():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM items")
    for item in DESIGNER_ITEMS:
        popularity = random.randint(60, 100)
        c.execute("""
            INSERT INTO items (brand,name,category,price,image_url,popularity,last_updated)
            VALUES (?,?,?,?,?,?,?)
        """, (*item, popularity, datetime.utcnow()))
    conn.commit()
    conn.close()

# -----------------------
# Ensure DB is populated before first request
# -----------------------
@app.before_first_request
def setup():
    init_db()
    update_items()

# -----------------------
# API Routes
# -----------------------
@app.route("/trending")
def trending():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT brand,name,category,price,image_url,popularity FROM items ORDER BY popularity DESC")
    data = [{
        "brand": r[0],
        "name": r[1],
        "category": r[2],
        "price": r[3],
        "image": r[4],
        "popularity": r[5]
    } for r in c.fetchall()]
    conn.close()
    return jsonify(data)

@app.route("/brand/<brand>")
def brand_items(brand):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name,category,price,popularity,image_url FROM items WHERE brand=? ORDER BY popularity DESC", (brand,))
    data = [{
        "name": r[0],
        "category": r[1],
        "price": r[2],
        "popularity": r[3],
        "image": r[4]
    } for r in c.fetchall()]
    conn.close()
    return jsonify(data)

# -----------------------
# Frontend
# -----------------------
@app.route("/")
def home():
    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Trending Designer Items</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="//unpkg.com/alpinejs" defer></script>
    </head>
    <body class="bg-gray-100 font-sans">
        <div class="container mx-auto p-6" x-data="app()">
            <h1 class="text-4xl font-bold text-center mb-8">🔥 Trending Designer Items</h1>

            <!-- Brand Tabs -->
            <div class="flex justify-center gap-4 mb-8 flex-wrap">
                <template x-for="b in brands" :key="b">
                    <button @click="selectBrand(b)"
                        :class="selectedBrand===b ? 'bg-black text-white' : 'bg-white text-black border border-gray-300'"
                        class="px-5 py-2 rounded-lg font-semibold transition-colors">
                        <span x-text="b"></span>
                    </button>
                </template>
            </div>

            <!-- Items Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                <template x-for="item in items" :key="item.name">
                    <div class="bg-white rounded-xl shadow-lg p-4 flex flex-col items-center hover:scale-105 transition-transform">
                        <img :src="item.image" class="h-40 w-40 object-cover rounded-lg mb-3" />
                        <h3 class="font-bold text-lg" x-text="item.name"></h3>
                        <p class="text-gray-500" x-text="item.category"></p>
                        <p class="text-gray-700 font-semibold mt-1" x-text="'$'+item.price"></p>
                        <p class="text-yellow-500 mt-1" x-text="'Popularity: '+item.popularity"></p>
                    </div>
                </template>
            </div>
        </div>

        <script>
        function app() {
            return {
                brands: ['Gucci','Prada','Balenciaga','Louis Vuitton','Dior','Off-White'],
                selectedBrand: 'Gucci',
                items: [],
                init() {
                    this.fetchBrand(this.selectedBrand)
                },
                selectBrand(brand) {
                    this.selectedBrand = brand;
                    this.fetchBrand(brand)
                },
                fetchBrand(brand) {
                    fetch('/brand/' + brand)
                        .then(res => res.json())
                        .then(data => this.items = data)
                        .catch(err => console.log(err))
                }
            }
        }
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

# -----------------------
# Main
# -----------------------
if __name__ == "__main__":
    # Run Flask without debug mode (Render-friendly)
    app.run(host="0.0.0.0", port=5000)
