import uuid
from database import SessionLocal
from models import Image

db = SessionLocal()
query_id = uuid.UUID("cd45a523-eb42-4382-bb87-98b2c7fb4aac")

img = db.query(Image).filter(Image.id == query_id).first()
if img:
    print(f"Found with UUID: {img.filepath}")
else:
    print("NOT FOUND with UUID object")
    
query_id_str = "cd45a523eb424382bb8798b2c7fb4aac"
img2 = db.query(Image).filter(Image.id == query_id_str).first()
if img2:
    print(f"Found with str without hyphens: {img2.filepath}")
else:
    print("NOT FOUND with str without hyphens")
