from sqlalchemy.orm import Session
from models import *
from sqlalchemy import select


class CategoryRepository:
    __session: Session
    def __init__(self, session: Session):
        self.__session = session

    def add(self, category: Category) -> Category:
        self.__session.add(category)
        return category
    def get_all(self) -> list[Category]:
        stmt = select(Category)

        return self.__session.scalars(stmt).all()
    def get_by_id(self, category_id: int) -> Category | None:
        stmt = select(Category).where(Category.category_id == category_id)
        return self.__session.scalar(stmt)
    


    


