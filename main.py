from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiomysql
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# MySQL database configuration
db_config = {
    'host': 'docker.lala-1992.xyz',
    'user': 'root',
    'password': 'rashmikamanawadu',
    'db': 'myapidb',
    'port': 3306
}

class UserInfo(BaseModel):
    username: str
    email: str
    userID: int
    userDomain: str

async def insert_into_database(user_info: UserInfo):
    conn = None
    try:
        logger.info(f"Attempting to connect to database with config: {db_config}")
        conn = await aiomysql.connect(**db_config)
        logger.info("Database connection established")
        
        async with conn.cursor() as cursor:
            # Check if userID already exists
            sql_check = "SELECT * FROM users WHERE userID = %s"
            await cursor.execute(sql_check, (user_info.userID,))
            existing_user = await cursor.fetchone()
            if existing_user is not None:
                return {"message": f"Username with userID {user_info.userID} already exists."}
            # Insert new user
            sql_insert = "INSERT INTO users (username, userID, email, domain_name) VALUES (%s, %s, %s, %s)"
            await cursor.execute(sql_insert, (user_info.username, user_info.userID, user_info.email, user_info.userDomain))
            await conn.commit()
            return {"message": "User inserted successfully."}
    except aiomysql.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

@app.post("/create_folder/")
async def create_folder(user_info: UserInfo):
    parent_folder = "users"  # The name of the pre-existing folder
    folder_name = f"user_{user_info.userID}"
    full_path = os.path.join(parent_folder, folder_name)
    
    try:
        # Ensure the parent folder exists
        Path(parent_folder).mkdir(exist_ok=True)
        
        # Create the user folder inside the parent folder
        Path(full_path).mkdir(exist_ok=True)
        logger.info(f"Folder '{full_path}' created successfully")
        
        # You can optionally insert the user info into the database here as well
        response = await insert_into_database(user_info)
        
        return {"message": f"Folder '{full_path}' created successfully and {response['message']}"}
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")

@app.post("/create_text_file/")
async def create_text_file(user_info: UserInfo):
    filename = f"user_{user_info.userID}.txt"
    file_content = f"Username: {user_info.username}\nEmail: {user_info.email}\nUserID: {user_info.userID}\nDomainname: {user_info.userDomain}"
    try:
        # Write to text file
        with open(filename, 'w') as file:
            file.write(file_content)
        logger.info(f"Text file '{filename}' created")
        
        # Insert into database asynchronously
        response = await insert_into_database(user_info)
        return {"message": f"Text file '{filename}' created and {response['message']}"}
    except HTTPException as he:
        logger.error(f"HTTP exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in create_text_file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create file or insert into database: {str(e)}")

@app.post("/push_data_db/")
async def push_data_db(user_info: UserInfo):
    try:
        response = await insert_into_database(user_info)
        return response
    except HTTPException as he:
        logger.error(f"HTTP exception in push_data_db: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in push_data_db: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to insert into database: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)