import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    email = Column(String(80), nullable = True)
    picture = Column(String(250), nullable = True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
        }

 
class Restaurant(Base):
    __tablename__ = 'restaurant'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id
        }
 
class MenuItem(Base):
    __tablename__ = 'menu_item'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    restaurant_id = Column(Integer, ForeignKey('restaurant.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    restaurant = relationship(Restaurant) 
    user = relationship(User)

# Add this is serializable methods to send JSON responses
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name' : self.name,
            'description': self.description,
            'price': self.price,
            'course': self.course,
            'user_id': self.user_id
        }
 



engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.create_all(engine)