from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class RAGSchema(BaseModel):
    text: Annotated[str, Field(min_length=1)]
    model_config = ConfigDict(str_strip_whitespace=True)

class ChatMessage(BaseModel):
    role: Literal['user','model']
    content:str

class ChatSchema(BaseModel):
    history: Annotated[list[ChatMessage], Field(min_items=1)]