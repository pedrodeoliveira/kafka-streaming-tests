from fastapi import FastAPI
import logging
import os
import uvicorn
from pydantic import BaseModel


from common import generate_random_output_data


MAX_INFERENCE_TIME_MS = int(os.getenv('MAX_INFERENCE_TIME_MS', 50))

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
log = logging.getLogger(__name__)


class TextCategorizationInput(BaseModel):
    uid: str
    text: str


class TextCategorizationOutput(BaseModel):
    uid: str
    text: str
    category: str
    subcategory: str
    confidence: float
    model: str
    version: int


# instantiate FastAPI
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    log.info(f'Starting FastAPI ...')


@app.post("/predict", response_model=TextCategorizationOutput)
async def predict(body: TextCategorizationInput):
    log.debug(f'Receive the following text to categorize: {body.text}')
    output_data = generate_random_output_data(body)

    random_inference_time_ms = randint(0, MAX_INFERENCE_TIME_MS)
    logger.debug(f'inference_time_ms: {random_inference_time_ms}')
    await asyncio.sleep(random_inference_time_ms / 1000)

    log.debug(f'Predicted category: {output_data['subcategory']}')
    response = TextCategorizationOutput(**output_data)
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)