from pydantic import BaseModel


class DefaultResp(BaseModel):
    response: str
