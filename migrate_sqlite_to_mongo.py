import sqlite3
from pymongo import MongoClient

# === SQLite setup ===
sqlite_path = "instance/site.db"
conn = sqlite3.connect(sqlite_path)
cursor = conn.cursor()

# Change this if your table name is different (e.g. "posts" or "blog_posts")
cursor.execute("SELECT * FROM post")
rows = cursor.fetchall()
columns = [col[0] for col in cursor.description]

# === MongoDB setup ===
mongo_uri = "mongodb+srv://kinkidycodes_db_user:OEWQOMMnhCVpi1nq@cluster0.gr5gqyd.mongodb.net/blog?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client["blog"]
collection = db["posts"]

# === Migrate data ===
migrated = 0
for row in rows:
    doc = dict(zip(columns, row))
    # Avoid duplicate _id fields if SQLite uses IDs
    doc.pop("id", None)
    collection.insert_one(doc)
    migrated += 1

print(f"Migration complete! {migrated} posts moved to MongoDB.")

conn.close()
client.close()
