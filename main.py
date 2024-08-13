import uuid, os, asyncio, time
from typing import Union
from pydantic import BaseModel
from fastapi import BackgroundTasks, FastAPI
from kling import VideoApi, ImageApi

app = FastAPI()


@app.get("/")
def index():
    return {"Hello": "World"}

class ImageReq(BaseModel):
    token: str
    prompt: str
    image_url: Union[str, None] = None

class VideoReq(BaseModel):
    token: str
    prompt: str
    image_url: Union[str, None] = None


@app.post("/image/create")
async def create_image(req: ImageReq, background_task: BackgroundTasks):
    api = ImageApi(req.token)
    try:
        task_id = api.create_task(req.prompt)
    except Exception as e:
        print(e)
        raise
    return {"task_id": task_id}


@app.get("/task/result")
def task_result(token: str, task_id: str, type: str = "image"):
    if type == "video":
        api = VideoApi(token)
        urls, status = api.get_task(task_id)
    else:
        api = ImageApi(token)
        urls, status = api.get_task(task_id)
    print(urls, status)
    return {
        "status":status,
        "urls": urls
    }

@app.post("/video/create")
def create_video( req: VideoReq):
    api = VideoApi(req.token)
    try:
        task_id = api.create_task(req.prompt)
    except Exception as e:
        print(e)
        raise
    return {"task_id": task_id}

@app.post("/test")
def test(background_task: BackgroundTasks):
    try:
     background_task.add_task(async_test)
    except Exception as e:
        print(e)
        raise
    return {"Hello": "World"}

def async_test():
    time.sleep(5)
    print(1111)
    return