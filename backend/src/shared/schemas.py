from pydantic import BaseModel


# Response with only a translated message for the user: {"message": "..."}
class MessageResponse(BaseModel):
    message: str
