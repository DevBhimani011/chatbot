from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_connection
from app.api.deps import get_current_admin_user
from app.core.queue import get_mq_client
import psycopg2.extras
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crawler", tags=["Crawler"])

class CrawledUrl(BaseModel):
    id: UUID
    url: str
    status: str
    last_crawled_at: Optional[datetime]
    created_at: datetime

class CreateUrlRequest(BaseModel):
    url: str

@router.get("/urls", response_model=List[CrawledUrl])
def get_urls(current_user: dict = Depends(get_current_admin_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT * FROM crawled_url ORDER BY created_at DESC")
        urls = cur.fetchall()
        return urls
    finally:
        cur.close()
        conn.close()

@router.post("/urls", response_model=CrawledUrl)
async def add_url(request: CreateUrlRequest, current_user: dict = Depends(get_current_admin_user)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO crawled_url (url, status) VALUES (%s, 'pending') RETURNING *",
            (request.url,)
        )
        url = cur.fetchone()
        conn.commit()
        
        # Trigger crawl automatically
        url_id = url['id']
        url_str = url['url']
        
        try:
            mq = await get_mq_client()
            await mq.publish_message("crawler_queue", {
                "url_id": str(url_id),
                "url": url_str
            })
        except Exception as e:
            logger.error(f"Failed to auto-trigger crawl for {url_str}: {e}")
            # Don't fail the request, just log it. The user can manually retry.
            
        return url
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="URL already exists")
    finally:
        cur.close()
        conn.close()

@router.delete("/urls/{url_id}")
def delete_url(url_id: UUID, current_user: dict = Depends(get_current_admin_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM crawled_url WHERE id = %s RETURNING id", (str(url_id),))
        deleted_id = cur.fetchone()
        if not deleted_id:
            raise HTTPException(status_code=404, detail="URL not found")
        conn.commit()
        return {"status": "success", "message": "URL deleted"}
    finally:
        cur.close()
        conn.close()

@router.post("/urls/{url_id}/crawl")
async def crawl_url(url_id: UUID, current_user: dict = Depends(get_current_admin_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if URL exists and get its value
        cur.execute("SELECT url FROM crawled_url WHERE id = %s", (str(url_id),))
        result = cur.fetchone()
        if not result:
             raise HTTPException(status_code=404, detail="URL not found")
        
        url_str = result[0]

        # Update status to pending (in case it was failed/completed)
        cur.execute("UPDATE crawled_url SET status = 'pending' WHERE id = %s", (str(url_id),))
        conn.commit()
        
        # Initialise MQ client (async)
        mq = await get_mq_client()
        
        # Publish task
        await mq.publish_message("crawler_queue", {
            "url_id": str(url_id),
            "url": url_str
        })

        return {"status": "queued", "message": f"Crawling started for {url_str}"}
    except Exception as e:
        logger.error(f"Error queuing crawl task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
