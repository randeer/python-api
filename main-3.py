from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import aiomysql

app = FastAPI()

# MySQL database configuration
db_config = {
    'host': 'docker.lala-1992.xyz',
    'user': 'root',
    'password': 'rashmikamanawadu',
    'db': 'myapidb',
    'port': 3306  # Add this line to specify the port explicitly
}

class UserInfo(BaseModel):
    username: str
    email: str
    userID: int
    userDomain: str

async def insert_into_database(user_info: UserInfo):
    conn = None
    try:
        conn = await aiomysql.connect(**db_config)
        if not conn:
            raise Exception("Failed to establish database connection")
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.post("/create_text_file/")
async def create_text_file(user_info: UserInfo):
    filename = f"user_{user_info.userID}.txt"
    file_content = f"Username: {user_info.username}\nEmail: {user_info.email}\nUserID: {user_info.userID}\nDomainname: {user_info.userDomain}"
    try:
        # Write to text file
        with open(filename, 'w') as file:
            file.write(file_content)
        # Insert into database asynchronously
        response = await insert_into_database(user_info)
        return {"message": f"Text file '{filename}' created and {response['message']}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file or insert into database: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)