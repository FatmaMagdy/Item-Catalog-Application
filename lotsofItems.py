from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Categories, Base, Items, User

engine = create_engine('sqlite:///itemCatalogWithUsers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Menu for Soccer
Soccer = Categories(user_id=1, name="Soccer")

session.add(Soccer)
session.commit()

item1 = Items(user_id=1, name="Foot Ball", description="Round black and white football.",
                     price="$7.50", categories=Soccer)

session.add(item1)
session.commit()


item2 = Items(user_id=1, name="shin guard", description="protects the shin and fits perfectly.",
                     price="$11.99", categories=Soccer)

session.add(item2)
session.commit()

item3 = Items(user_id=1, name="Jersey", description="Messi number 10 Jersey.",
                     price="$19.50", categories=Soccer)

session.add(item3)
session.commit()



# Menu for BasketBall
BasketBall = Categories(user_id=1, name="BasketBall")

session.add(BasketBall)
session.commit()


item1 = Items(user_id=1, name="BasketBall", description="Orange Stanford basketball.",
                     price="$10.99", categories=BasketBall)

session.add(item1)
session.commit()

item2 = Items(user_id=1, name="BasketBall shoes",
                     description=" A famous NBA Nike Air shoes.", price="$100", categories=BasketBall)

session.add(item2)
session.commit()

item3 = Items(user_id=1, name="BasketBall Bag", description="shoulder strap bag to hold the basket ball and the water bottle.",
                     price="15", categories=BasketBall)

session.add(item3)
session.commit()


# Menu for SnowBording
SnowBording = Categories(user_id=1, name="SnowBording")

session.add(SnowBording)
session.commit()


item1 = Items(user_id=1, name="Snowboard", description="All mountain sow board.",
                     price="$8.99", categories=SnowBording)

session.add(item1)
session.commit()

item2 = Items(user_id=1, name="SnowBording Helmet", description="Green SnowBoarding Helmet.",
                     price="$18.99", categories=SnowBording)

session.add(item2)
session.commit()

item3 = Items(user_id=1, name="Snowboard Goggles", description="Face mask to protect your eyes.",
                     price="$10.95", categories=SnowBording)
                     

session.add(item3)
session.commit()



print "added menu items!"
