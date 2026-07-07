from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve index.html at "/" and every other file (support.js, image-slot.js,
# assets/, .image-slots.state.json) as static content.
app.mount("/", StaticFiles(directory=".", html=True), name="site")
