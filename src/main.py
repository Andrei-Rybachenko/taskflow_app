import uvicorn
from fastapi import FastAPI


app = FastAPI(title="TaskFlow",
              description="Система управления бизнесом для трекинга команд и их задач",
              version="1.0.1"
              )

@app.get("/")
async def get_root():
    return {"message": "Добро пожаловать!"}



if __name__ == "__main__":
    pass
    # uvicorn.run(app="src.main:app", reload=True)