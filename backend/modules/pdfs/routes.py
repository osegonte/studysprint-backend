"""PDF API routes - Basic placeholder for Stage 1"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_pdfs():
    """Placeholder endpoint for PDF listing"""
    return {
        "message": "PDFs module placeholder - Stage 1",
        "status": "coming_soon",
        "scheduled_implementation": "Day 2 of Stage 1"
    }

# TODO: Implement PDF endpoints in Day 2
# - POST /api/pdfs/upload
# - POST /api/pdfs/{study_pdf_id}/attach-exercise
# - GET /api/pdfs/
# - GET /api/pdfs/{id}
# - GET /api/pdfs/{id}/content
# - GET /api/pdfs/{id}/thumbnail
# - DELETE /api/pdfs/{id}
# - GET /api/pdfs/search