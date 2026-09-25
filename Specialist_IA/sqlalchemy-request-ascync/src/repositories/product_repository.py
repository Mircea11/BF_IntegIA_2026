from sqlalchemy.orm import Session
from models import Product, Category
from sqlalchemy import select


class ProductRepository:
    __session: Session
    def __init__(self, session: Session):
        self.__session = session


        #CRUD
        
        #CREATE
    def add(self, product: Product):
            self.__session.add(product)
            return product

        #READ
    def get_all(self):
            stmt = select(Product)

            return self.__session.scalars(stmt).all()
        # UPDATE
    # def update(self, product: Product):
    #             self.__session.(product)
    #             return product
        
        # DELETE
    def delete(self, product: Product):
        self.__session.delete(product)
        return product
        