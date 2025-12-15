import aiohttp
import io
import cv2
import numpy as np
import torch
from typing import Union
from PIL import Image, ImageFile, ImageStat
from transformers import CLIPProcessor, CLIPModel

ImageFile.LOAD_TRUNCATED_IMAGES = True

# lazy-load models (initialize once globally or in a class)
_clip_model = None
_clip_processor = None

def _get_clip_model():
    global _clip_model, _clip_processor
    if _clip_model is None:
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        _clip_model.eval()
    return _clip_model, _clip_processor

async def _load_image_bytes_from_url(url: str) -> bytes:
    async with aiohttp.ClientSession(trust_env=True) as s:
        async with s.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()

def _load_image_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b))

def _check_blur(img_cv: np.ndarray, threshold: float = 50.0) -> float:
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY) if len(img_cv.shape) == 3 else img_cv
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Old calculation:
    # score = min(1.0, lap_var / 100.0)  # → 38/100 = 0.38
    
    # New calculation (divide by 50 instead of 100):
    score = min(1.0, lap_var / 50.0)  # → 38/50 = 0.76 ✓
    return float(score)

def _check_contrast(img_pil: Image.Image, min_stddev: float = 30.0) -> float:
    """
    Stddev-based contrast check. Returns 0..1 (1=good contrast, 0=flat).
    """
    gray = img_pil.convert("L")
    stat = ImageStat.Stat(gray)
    stddev = stat.stddev[0] if stat.stddev else 0.0
    score = min(1.0, stddev / min_stddev)
    return float(score)

def _check_aesthetic_clip(img_pil: Image.Image, prompt: str = "high quality, beautiful") -> float:
    """
    CLIP similarity to aesthetic prompt. Returns 0..1 (higher = more aesthetically pleasing).
    """
    model, processor = _get_clip_model()
    inputs = processor(text=[prompt], images=img_pil, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        image_emb = outputs.image_embeds / outputs.image_embeds.norm(dim=-1, keepdim=True)
        text_emb = outputs.text_embeds / outputs.text_embeds.norm(dim=-1, keepdim=True)
        similarity = (image_emb @ text_emb.T).item()
    # CLIP similarity is roughly [-1,1], shift to [0,1]
    score = (similarity + 1.0) / 2.0
    return max(0.0, min(1.0, score))

async def score_image(path_or_url: str, prompt: str = "high quality, beautiful") -> float:
    """
    Two-stage scoring:
    1. Technical quality (blur, contrast) - must pass thresholds
    2. Aesthetic quality (CLIP similarity) - final score
    Returns 0.0..1.0 (weighted composite).
    """
    try:
        if path_or_url.startswith("http"):
            b = await _load_image_bytes_from_url(path_or_url)
        else:
            with open(path_or_url, "rb") as f:
                b = f.read()
        img_pil = _load_image_from_bytes(b)
        img_cv = np.array(img_pil.convert("RGB"))
    except Exception as e:
        print(f"Failed to load image: {e}")
        return 0.0

    try:
        # Stage 1: technical checks
        blur_score = _check_blur(img_cv)  # Uses default 50.0
        contrast_score = _check_contrast(img_pil, min_stddev=30.0)
        
        # If either technical metric is too low, fail early
        if blur_score < 0.3 or contrast_score < 0.4:  # Lower thresholds for stock photos
            print(f"Technical quality low: blur={blur_score:.2f}, contrast={contrast_score:.2f}")
            return 0.0

        # Stage 2: aesthetic (CLIP)
        aesthetic_score = _check_aesthetic_clip(img_pil, prompt=prompt)
        
        # Weighted composite: 30% blur, 20% contrast, 50% aesthetic
        final_score = 0.3 * blur_score + 0.2 * contrast_score + 0.5 * aesthetic_score
        
        print(f"Scores: blur={blur_score:.2f}, contrast={contrast_score:.2f}, aesthetic={aesthetic_score:.2f} -> final={final_score:.2f}")
        return max(0.0, min(1.0, final_score))
    except Exception as e:
        print(f"Error scoring image: {e}")
        return 0.0