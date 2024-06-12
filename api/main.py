from contextlib import asynccontextmanager
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import shutil
from typing import List, Dict
from pathlib import Path
import plotly.express as px
import plotly.io as pio

# File paths
PENGUINS_FILE = "penguins.csv"
PENGUINS_ORIGINAL_FILE = "penguins_original.csv"


def initialize_penguins_file():
    if not Path(PENGUINS_FILE).exists() or not Path(PENGUINS_FILE).read_text():
        shutil.copyfile(PENGUINS_ORIGINAL_FILE, PENGUINS_FILE)


def getCsvAsJson(file):
    df = pd.read_csv(file)
    return df.to_dict(orient='records')


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_penguins_file()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
        df.to_csv(PENGUINS_FILE, index=False)
        return {"message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An error occurred: {e}")


@app.get("/data")
async def get_csv() -> List[Dict]:
    return getCsvAsJson(PENGUINS_FILE)


@app.get("/scatter-plot")
async def get_scatter_plot(x: str, y: str, color: str, flipper_length_min: int = 0):
    df = pd.read_csv(PENGUINS_FILE)
    df = df[df['flipper_length_mm'] >= flipper_length_min]
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        title='Penguin Bill Length vs Bill Depth',
        labels={
            'bill_length_mm': 'Bill Length (mm)', 'bill_depth_mm': 'Bill Depth (mm)'}
    )
    return JSONResponse(content=pio.to_json(fig))


@app.get("/histogram")
async def get_histogram(column: str, color: str, flipper_length_min: int = 0):
    df = pd.read_csv(PENGUINS_FILE)
    df = df[df['flipper_length_mm'] >= flipper_length_min]
    fig = px.histogram(
        df, 
        x=column, 
        color=color, 
        title='Penguin Bill Length vs Bill Depth', 
        labels={'bill_length_mm': 'Bill Length (mm)', 'bill_depth_mm': 'Bill Depth (mm)'}
    )
    return JSONResponse(content=pio.to_json(fig))


@app.get("/render/{plot}")
async def get_plotly(plot: str) -> List[Dict]:
    df = getCsvAsJson(PENGUINS_FILE)
    fig = None

    if (plot != "plot"):
        fig = px.scatter(
            df,
            x='bill_length_mm',
            y='bill_depth_mm',
            color='species',
            title='Penguin Bill Length vs Bill Depth',
            labels={
                'bill_length_mm': 'Bill Length (mm)', 'bill_depth_mm': 'Bill Depth (mm)'}
        )
    else:
        fig = px.histogram(
            df,
            x='bill_length_mm',
            color='species',
            title='Histogram of Bill Length by Species',
            labels={'bill_length_mm': 'Bill Length (mm)'}
        )

    html_content = fig.to_html(full_html=False)
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
