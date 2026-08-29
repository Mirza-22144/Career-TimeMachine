

from fastapi import APIRouter

# a mini-router this file owns
router=APIRouter() 

@router.get ("/health")
def health():
    return {"status": "ok"}




