
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# lire . enc et transforme les constatnes en variables  d'environment
load_dotenv() 

engine = create_engine(os.getenv('DB_URL'))


def GetSession():
    return sessionmaker(bind=engine)()