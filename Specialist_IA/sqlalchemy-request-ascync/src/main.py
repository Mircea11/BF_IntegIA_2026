from models import *
from repositories.category_repository import CategoryRepository
from repositories.product_repository import ProductRepository
#from repositories import ProductRepository

Base.metadata.create_all(bind=engine)


with GetSession() as session:
    category_repo = CategoryRepository(session)
    product_repo = ProductRepository(session)

    pizza_category = category_repo.get_by_id(1)
    print(pizza_category)

    # pizza_category = Category(category_id=1,category_name = 'pizza')
    # category_repo.add(pizza_category)

    # session.commit
    #session.rollback

    for category in category_repo.get_all():
        print(f"{category.category_id} - {category.category_name}")

    # pizza1 = Product(2, 'Pizza capricciosa', 16, pizza_category.category_id)
    # pizza2 =Product(1, 'Pizza 4 fromages', 14.5, pizza_category.category_id)
    # pizza3 =Product(3, 'Pizza napolitaine', 12, pizza_category.category_id)
    # pizza4 =Product(4, 'Pizza hawaienne', 13.2, pizza_category.category_id)

    # product_repo.add(pizza1)
    # product_repo.add(pizza2)
    # product_repo.add(pizza3)
    # product_repo.add(pizza4)

    # session.commit()

    Pizza4fromages = product_repo.get_all()[0]
    print(Pizza4fromages.product_price)

    Pizza4fromages.product_price = 20
    print(Pizza4fromages.product_price)
    session.commit()
    print(Pizza4fromages.product_price)
    # session.rollback()
    # print(Pizza4fromages.product_price)
    #session.rollback() pour revenir les resultats

    for pizza in product_repo.get_all():
        print(pizza)






