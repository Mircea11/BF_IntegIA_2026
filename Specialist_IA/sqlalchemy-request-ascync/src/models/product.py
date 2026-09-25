
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from models import Base
if TYPE_CHECKING:
    from models import Category

class Product(Base):
    __tablename__ = 'products'
    product_id:Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column()
    product_price: Mapped[float] = mapped_column()
    category_id: Mapped[int] = mapped_column(
        ForeignKey('categories.category_id')
             )
    
    category:Mapped["Category"] = relationship(
        back_populates='products',
        init=False
    )

     