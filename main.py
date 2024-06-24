from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiomysql
import logging
import os
from pathlib import Path
import shutil
import yaml

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

class FolderInfo(BaseModel):
    userID: int

@app.post("/copy_template_folder/")
async def copy_template_folder(folder_info: FolderInfo):
    parent_folder = "users"
    user_folder = f"user_{folder_info.userID}"
    full_path = os.path.join(parent_folder, user_folder)
    template_folder = "k8s-template"
    
    try:
        # Check if the user folder exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"User folder '{full_path}' not found")
        
        # Copy the entire k8s-template folder to the user folder
        dst_folder = os.path.join(full_path, os.path.basename(template_folder))
        shutil.copytree(template_folder, dst_folder)
        
        logger.info(f"Copied {template_folder} to {dst_folder}")
        return {"message": f"Template folder copied to '{dst_folder}' successfully"}
    except FileNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to copy template folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to copy template folder: {str(e)}")

async def update_template_file(user_info: UserInfo):
    parent_folder = "users"
    user_folder = f"user_{user_info.userID}"
    template_file = os.path.join(parent_folder, user_folder, "k8s-template", "issuer_template.yml")
    
    try:
        # Read the template file
        with open(template_file, 'r') as file:
            content = file.read()
        
        # Replace placeholders
        content = content.replace('{{ userID }}', str(user_info.userID))
        content = content.replace('{{ email }}', user_info.email)
        
        # Parse the updated content as YAML
        yaml_content = yaml.safe_load(content)
        
        # Write the updated YAML back to the file
        with open(template_file, 'w') as file:
            yaml.dump(yaml_content, file, default_flow_style=False)
        
        logger.info(f"Template file '{template_file}' updated successfully")
        return {"message": f"Template file '{template_file}' updated successfully"}
    except FileNotFoundError:
        logger.error(f"Template file '{template_file}' not found")
        raise HTTPException(status_code=404, detail=f"Template file '{template_file}' not found")
    except Exception as e:
        logger.error(f"Failed to update template file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update template file: {str(e)}")

@app.post("/update_template_file/")
async def update_template_file_endpoint(user_info: UserInfo):
    return await update_template_file(user_info)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)