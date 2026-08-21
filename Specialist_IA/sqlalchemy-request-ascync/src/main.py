from models import *
from repositories.category_repository import CategoryRepository

Base.metadata.create_all(bind=engine)


with GetSession() as session:
    category_repo = CategoryRepository(session)

    pizza_category = Category(category_id=1,category_name = 'pizza')
    category_repo.add(pizza_category)

    session.commit
    #session.rollback

    for category in category_repo.get_all():
        print(f"{category.category_id} - {category.category_name}")

    



