from plugin.database import init_engine
from plugin import models
import uvicorn
from fastapi import FastAPI


# Binds metadata to engine created with default config
models.Base.metadata.create_all(bind=init_engine(pool_pre_ping=True, executemany_mode="values_plus_batch"))

app = FastAPI(title='DMSS Plugin')

if __name__ == "__main__":
    uvicorn.run(app)
