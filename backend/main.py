from contextlib import asynccontextmanager
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from services.scraper import scrape_article
from services.bias_analyzer import analyze_political_bias, preload_models as _preload_bias
from services.source_checker import check_source_credibility
from services.framing_analyzer import analyze_framing, preload_models as _preload_framing

logger = logging.getLogger("news-bias-detector")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Preloading ML models (this may take a minute on first run)...")
    loop = asyncio.get_event_loop()
    try:
        await asyncio.gather(
            loop.run_in_executor(None, _preload_bias),
            loop.run_in_executor(None, _preload_framing),
        )
        logger.info("Models ready.")
    except Exception as exc:
        logger.warning("Model preload failed — will load on first request: %s", exc)
    yield


app = FastAPI(title="News Bias Detector API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    political_lean: dict
    source_credibility: dict
    framing: dict
    summary: str
    article_title: Optional[str] = None
    source_domain: Optional[str] = None
    word_count: int = 0


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    if not request.text and not request.url:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'url'")

    article_text = request.text
    source_domain: Optional[str] = None
    article_title: Optional[str] = None

    if request.url:
        try:
            scraped = await asyncio.to_thread(scrape_article, request.url)
            article_text = scraped["text"]
            source_domain = scraped["domain"]
            article_title = scraped.get("title")
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Failed to fetch article: {exc}")

    if not article_text or len(article_text.strip()) < 80:
        raise HTTPException(status_code=422, detail="Article text is too short to analyze")

    political, credibility, framing = await asyncio.gather(
        asyncio.to_thread(analyze_political_bias, article_text),
        asyncio.to_thread(check_source_credibility, source_domain),
        asyncio.to_thread(analyze_framing, article_text),
    )

    return AnalyzeResponse(
        political_lean=political,
        source_credibility=credibility,
        framing=framing,
        summary=_build_summary(political, credibility, framing),
        article_title=article_title,
        source_domain=source_domain,
        word_count=len(article_text.split()),
    )


def _build_summary(political: dict, credibility: dict, framing: dict) -> str:
    parts: list[str] = []

    lean = political["label"]
    conf = political["confidence"]
    lean_labels = {
        "far-left": "strongly left-leaning",
        "left": "politically left-leaning",
        "lean-left": "slightly left-leaning",
        "center": "politically centrist",
        "lean-right": "slightly right-leaning",
        "right": "politically right-leaning",
        "far-right": "strongly right-leaning",
    }
    lean_text = lean_labels.get(lean, lean)
    parts.append(f"This article appears {lean_text} (confidence: {conf:.0%})")

    loaded = framing["loaded_language_score"]
    if loaded > 0.6:
        parts.append("contains heavy loaded or emotionally charged language")
    elif loaded > 0.3:
        parts.append("uses some emotionally charged language")
    else:
        parts.append("language is mostly neutral")

    if credibility["found"] and credibility["score"] is not None:
        outlet = credibility["outlet"]
        score = credibility["score"]
        if score >= 8:
            parts.append(f"source '{outlet}' is generally considered highly credible")
        elif score >= 5:
            parts.append(f"source '{outlet}' has mixed to moderate credibility")
        else:
            parts.append(f"source '{outlet}' has low credibility")

    tone = framing.get("opening_tone", "neutral")
    if tone != "neutral":
        parts.append(f"the opening framing has a {tone} tone")

    return "; ".join(parts) + "."


@app.get("/health")
def health():
    return {"status": "ok"}
