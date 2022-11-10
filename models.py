from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()


#----------------------------------------------------------------------------#
########################     MODEL THE DATABASE    ##########################
#----------------------------------------------------------------------------#

#######################  VENUE MODEL  ######################

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    website_link = db.Column(db.String(250))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', passive_deletes= False, backref='venues', lazy=True)
    
    def __repr__(self):
      return f"<Venue {self.id} name: {self.name}>"
 
#######################  ARTIST MODEL  ######################

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    website_link = db.Column(db.String(250))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='artists', lazy=True)

    def __repr__(self):
      return f"<Artist {self.id} name: {self.name}>"

#######################  SHOW MODEL  ######################

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable = True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable = True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
      return f"<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>"

