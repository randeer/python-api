from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class UserInfo(BaseModel):
    username: str
    email: str
    userID: int
    userDomain: str

@app.post("/create_text_file/")
async def create_text_file(user_info: UserInfo):
    filename = f"user_{user_info.userID}.txt"
    file_content = f"Username: {user_info.username}\nEmail: {user_info.email}\nUserID: {user_info.userID}\nDomainname: {user_info.userDomain}"

    try:
        with open(filename, 'w') as file:
            file.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")

    return {"message": f"Text file '{filename}' created successfully."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
