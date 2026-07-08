from fastapi.responses import JSONResponse

class ServerError(JSONResponse):
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(status_code = 500, content = {"message": message})