from fastapi import FastAPI
from fastapi.security import HTTPBearer
from routes import user, measurement, graph 
 
from database import engine, Base 

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(user.router)
app.include_router(measurement.router)
app.include_router(graph.router)

@app.get("/")
def read_root():
    return {"Hello": "Airlzy FastAPI Server is running!"}