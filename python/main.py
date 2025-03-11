import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
import hashlib
import json


# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"


def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db,  check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


# STEP 5-1: set up the database connection
def setup_database():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    sql_file = pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"
    with open(sql_file, "r") as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.DEBUG
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
async def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    image = hash_image(image)
    insert_item(Item(name=name, category=category, image=image))
    insert_item_db(Item(name=name, category=category, image=image), db)
    return AddItemResponse(**{"message": f"item received: {name}"})


# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")
def get_image(image_name:str):
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image, media_type="image/jpeg")


class Item(BaseModel):
    name: str
    category: str
    image: str 

def insert_item(item: Item):
        # STEP 4-1: add an implementation to store an item
    with open('items.json', 'r') as f:
        data = json.load(f)
    data["items"].append({"name": item.name, "category": item.category, "image_name": item.image})
    with open('items.json', 'w') as f:
        json.dump(data, f, indent=4)


def insert_item_db(item: Item, conn: sqlite3.Connection):
    #step5
    cur = conn.cursor()
    with open("db/items.sql", "r") as f:
        cur.executescript(f.read())
    cur.execute("SELECT id FROM categories WHERE name = ?", (item.category,))
    category_data = cur.fetchone()
    if category_data is None:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (item.category,))
        category_id = cur.lastrowid 
    else:
        category_id = category_data["id"]
    cur.execute("INSERT INTO items (name, category_id, image_name) VALUES (?, ?, ?)", 
                (item.name, category_id, item.image))
    conn.commit()
    return

def hash_image(image: UploadFile):
    file_content = image.file.read()  
    hash_value = hashlib.sha256(file_content).hexdigest()
    rename = f"{hash_value}.jpg"
    image_path = images / rename
    with open(image_path, "wb") as f:
            f.write(file_content)  
    return rename


@app.get("/items")
def get_items(conn = Depends(get_db)):  
    cur = conn.cursor()
    cur.execute("""
        SELECT items.name, categories.name AS category, items.image_name 
        FROM items 
        JOIN categories ON items.category_id = categories.id
    """)
    raw = cur.fetchall()
    columns_names = [description[0] for description in cur.description]
    data = [dict(zip(columns_names, row)) for row in raw]
    return {"items": data} 
    

@app.get("/items/{id}")
def get_item_id(id: int, conn: sqlite3.Connection = Depends(get_db)):
    cur = conn.cursor()
    cur.execute(
        " SELECT * FROM items WHERE id = ?", (id,)
        )
    raw = cur.fetchall()
    columns_names = [description[0] for description in cur.description]
    data = [dict(zip(columns_names, row)) for row in raw]
    return {"items": data} 
    
    
@app.get("/search")
def serch_item(keyword: str, conn:sqlite3.Connection = Depends(get_db)):
    cur = conn.cursor()
    query = """
    SELECT items.name, categories.name AS category, items.image_name
    FROM items
    JOIN categories ON items.category_id = categories.id
    WHERE items.name = ?
    """
    cur.execute(query, (keyword,))
    raw = cur.fetchall()
    columns_names = [description[0] for description in cur.description]
    data = [dict(zip(columns_names, row)) for row in raw]
    return {"items": data} 
    