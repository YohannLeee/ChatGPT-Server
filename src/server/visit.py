# 
import logging
from fastapi import Depends, Response, Request, status, APIRouter, HTTPException, Body
from pydantic import BaseModel

from database import get_page_db, get_visit_db, get_visitor_db, BasePageDatabase, BasevisitDatabase, BasevisitorDatabase
from library.fastapi_users.authentication import Authenticator
from library.schemas import CreatePage, UpdatePage, BaseVisitor, CreateVisit, AuthedVisitor
from library.models import PP


log = logging.getLogger("app.server")

class VisitModel(BaseModel):
    url: str

def get_visit_router(
        authenticator: Authenticator,
    ):
    router = APIRouter()

    @router.post("/", name = "visit")
    async def visit(
        request: Request,
        url: str = Body(..., embed=True),
        page_db: BasePageDatabase= Depends(get_page_db),
        visit_db: BasevisitDatabase = Depends(get_visit_db),
        visitor_db: BasevisitorDatabase = Depends(get_visitor_db),
    ):
        # 1. Check page exist status
        # 2. Check visitor authed or not
        # 3. add visitor
        # 4. add visit record

        page = page_db.get_page_by_url(url)
        if not page:
            page = CreatePage(url = url)
            page = page_db.create(page)

        try:
            user = authenticator.current_user()
            page.authed_visit_count += 1
            visitor = AuthedVisitor(id = user.id, ip = request.headers["X-Forwarded-For"])
        except HTTPException:
            # visitor is not an authed user
            page.unauthed_visit_count += 1
            visitor = BaseVisitor(ip = request.headers["X-Forwarded-For"], user_agent= request.headers['User-Agent'])
            if not visitor_db.get_visitor(visitor):
                visitor = visitor_db.create(visitor_db)

        page_db.update(page)

        visit = CreateVisit(visitor_id= visitor.id, page_id = page.id)
        visit_db.create(visit)

