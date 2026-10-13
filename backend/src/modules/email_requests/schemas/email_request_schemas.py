from pydantic import BaseModel, EmailStr


# Body of POST /email-requests
class EmailRequestCreate(BaseModel):
    email: EmailStr
