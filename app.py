#----------------------------------------------------------------------------#
########################     IMPORT PYTHON MODULE  ###########################
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
import collections
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
########################     APP CONFIGURATION  ###########################
#----------------------------------------------------------------------------#
collections.Callable = collections.abc.Callable
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

from models import *

############ MIGRATION TO MANAGE DATABASE SCHEMA AND KEEP THE DATA ###########

migrate = Migrate(app, db)

#######################  FORMAT DATETIME FUNCTION  ######################

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
###############################  APP CONTROLLER  #############################
#----------------------------------------------------------------------------#

#######################  MAIN ROUTE ######################

@app.route('/')
def index():
  shows = Show.query.order_by(db.desc(Show.start_time)).limit(10)
  # artist = Artist.query.order_by(db.desc(shows.start_time))
  # artist = Artist.query.filter(id = shows.artist_id)
  data = []
  for show in shows:
    data.append({
      'artist_id': show.artist_id,
      'artist_name': show.artists.name,
      'artist_image_link': show.artists.image_link,
      'artist_state': show.artists.state,
      'venue_id': show.venue_id,
      'venue_name': show.venues.name,
      'venue_image_link': show.venues.image_link,
      'venue_state':show.venues.state
    })

  return render_template('pages/home.html', shows = data)

#######################  SHOW THE VENUE LIST ######################

@app.route('/venues')
def venues():
  
  data = []
  venues = Venue.query.all()
  region = set()

  for venue in venues:
    region.add((venue.city, venue.state))
  for region in region:
    data.append({
      "city": region[0],
      "state": region[1],
      "venues": []
    })
  for venue in venues:
    num_upcoming_shows = 0

    shows = Show.query.filter_by(venue_id=venue.id).all()
    
    current_date = datetime.now()

    for show in shows:
      if show.start_time > current_date:
        num_upcoming_shows += 1
    
    for venue_region in data:
      if venue.state == venue_region['state'] and venue.city == venue_region['city']:
        venue_region['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "image_link":venue.image_link,
          "phone":venue.phone,
          "num_upcoming_shows": num_upcoming_shows
        })
  return render_template('pages/venues.html', areas=data)


##########################  SEARCH VENUE ROUTE ###########################

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))

  response={
    "count": result.count(),
    "data": result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

#########################  SHOW THE VENUE ROUTE ITEM ######################

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

  past_show = []
  upcoming_show = []

  for show in past_shows:
        past_show.append({
            'artist_id': show.artist_id,
            'artist_name': show.artists.name,
            'artist_image_link': show.artists.image_link,
            "start_time": format_datetime(str(show.start_time))
        })

  for show in upcoming_shows:
    upcoming_show.append({
      'artist_id': show.artist_id,
      'artist_name': show.artists.name,
      'artist_image_link': show.artists.image_link, 
      "start_time": format_datetime(str(show.start_time))
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_show,
    "upcoming_shows": upcoming_show,
    "past_shows_count": len(past_show),
    "upcoming_shows_count": len(upcoming_show)
    }


  return render_template('pages/show_venue.html', venue=data)

#######################  CREATE A VENUE   ######################

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

#######################  SUBMIT CREATE VENUE   ######################

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  venu = VenueForm(request.form, meta={'csrf':False})
  if venu.validate():
    try:
      venue = Venue(name=venu.name.data, city=venu.city.data, state=venu.state.data, address=venu.address.data, phone=venu.phone.data, image_link=venu.image_link.data, genres=venu.genres.data, facebook_link=venu.facebook_link.data, website_link=venu.website_link.data, seeking_talent=venu.seeking_talent.data, seeking_description=venu.seeking_description.data)

      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + venu.name.data + ' was successfully listed!')
      return render_template('pages/home.html')

    except:
      flash('An error ocurred, Venue ' + venu.name.data + ' could not be listed')
      db.session.rollback()
    finally:
      db.session.close()
  else:
      message = []
      for field, err in venu.errors.items():
          message.append(field + ' ' + '|'.join(err))
      flash('Errors ' + str(message))
      return render_template('forms/new_venue.html', form=venu)

  return render_template('pages/venues.html')

#######################  DELETE VENUE   ######################

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get_or_404(venue_id)
    show = Show.query.filter_by(venue_id = venue_id).first()
    
    if show is not None:
      print('Show is not null')
      db.session.delete(show)
    else:
      print('Show is null')
    db.session.delete(venue)
    db.session.commit()

    flash('Venue ' + venue.name + ' was deleted')
  except:
    flash(' an error occured and Venue ' + venue.name + ' was not deleted')
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('index'))

#######################  SHOW THE ARTIST LIST  ######################

@app.route('/artists')
def artists():

  data = Artist.query.all()
  
  return render_template('pages/artists.html', artists = data)

#######################  SEARCH THE ARTIST   ######################

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term', '')
  result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  response = {
    'count': result.count(),
    'data': result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

#######################  SHOW THE ARTIST LIST  ######################

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
  
  past_show = []
  upcoming_show = []

  for show in past_shows:
    past_show.append({
      'artist_id': show.venue_id,
      'venue_name': show.venues.name,
      'venue_image_link': show.venues.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  for show in upcoming_shows:
    upcoming_show.append({
      'artist_id': show.artist_id,
      'venue_name': show.venues.name,
      'venue_image_link': show.venues.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_show,
    "upcoming_shows": upcoming_show,
    "past_shows_count": len(past_show),
    "upcoming_shows_count": len(upcoming_show)
  }


  return render_template('pages/show_artist.html', artist=data)

#######################  UPDATE THE CHOSEN ARTIST   ######################

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  form.name.data = artist.name 
  form.phone.data = artist.phone
  form.state.data = artist.state
  form.city.data = artist.city
  form.genres.data = artist.genres
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

########################## UPDATE THE CHOSEN ARTIST ########################

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  try:
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    
    artist.name = form.name.data
    artist.phone = form.phone.data
    artist.state = form.state.data
    artist.city = form.city.data
    artist.genres = form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website_link = form.website_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data

    db.session.commit()
    flash('The Artist ' + artist.name + ' has been successfully updated!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An Error has occured and the update is unsucessful')

  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))


########################### DELETE ARTIST ##########################

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  show = ShowForm()

  try:
    artist= Artist.query.get_or_404(artist_id)
    show = Show.query.filter_by(artist_id = artist_id).first()

    if show is not None:
      print('Show is not null')
      db.session.delete(show)
    else:
      print('Show is null')
    db.session.delete(artist)
    db.session.commit()

    flash('The ' + artist.name + ' was deleted')
  except:
    flash(' an error occured and Artist' + artist.name  +'was not deleted')
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))

  ########################### UPDATE CHOSEN VENUE  ############################

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  form = VenueForm()
  venue = Venue.query.get(venue_id)
  try:
    form.name.data = venue.name
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.state.data = venue.state
    form.city.data = venue.city
    form.genres.data = venue.genres
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    
  except:
    flash(' Venue ' + venue.name + ' will UPDATE')
    print(sys.exc_info())
  finally:
    db.session.close()

  return render_template('forms/edit_venue.html', form=form, venue=venue)

########################### SUBMIT THE UPDATE OF CHOSEN VENUE  ############################

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm()
  venue = Venue.query.get(venue_id)
  try:
    venue.name = form.name.data
    venue.address = form.address.data 
    venue.phone = form.phone.data
    venue.state = form.state.data
    venue.city = form.city.data
    venue.genres = form.genres.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.image_link = form.image_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data

    db.session.commit()
    flash('Venue ' + form.name.data + ' was successfully listed!')
  except:
    flash('An error ocurred, Venue ' + form.name.data + ' could not be listed')
    db.session.rollback()

  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

########################### CREATE A ARTIST  ############################

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

########################### SUBMIT CREATE ARTIST ############################

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta={'csrf':False})
  if form.validate():
    try:
      
      artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data, phone=form.phone.data, genres=form.genres.data,image_link=form.image_link.data, facebook_link=form.facebook_link.data, website_link=form.website_link.data, seeking_venue=form.seeking_venue.data, seeking_description=form.seeking_description.data)
      db.session.add(artist)
      db.session.commit()
    
      flash('Artist ' + form.name.data + ' was successfully listed!')
    except:
      flash('An error ocurred, Venue ' + request.form['name'] + ' could not be listed')
      db.session.rollback()
    finally:
      db.session.close()

  else:
      message = []
      for field, err in form.errors.items():
        message.append(field + ' ' + '|'.join(err))
      flash('Errors ' + str(message))

      return render_template('forms/new_artist.html', form=form)
  
  return render_template('pages/home.html')

########################### SHOW THE SHOWS PAGE ############################

@app.route('/shows')
def shows():
 
  shows = Show.query.order_by(db.desc(Show.start_time))

  data = []
  for show in shows:
    data.append({
      'venue_id': show.venues.id,
      'venue_name': show.venues.name,
      'artist_id': show.artist_id,
      'artist_name': show.artists.name,
      'artist_image_link': show.artists.image_link,
      'start_time': format_datetime(str(show.start_time))
    })

  return render_template('pages/shows.html', shows=data)

########################### CREATE THE SHOWS ############################

@app.route('/shows/create')
def create_shows():

  form = ShowForm()
  
  return render_template('forms/new_show.html', form = form)

########################### SUBMIT THE CREATE SHOWS ############################

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  try:
    show = ShowForm()
    shows = Show(artist_id  = show.artist_id.data, venue_id = show.venue_id.data, start_time = show.start_time.data)
    db.session.add(shows)
    db.session.commit()
  
    flash('Show was successfully listed!')
  except:
    flash('An error ocurred and the show could not be listed')
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/home.html')

  ########################### SEARCH THE SHOWS ############################

@app.route('/shows/search', methods=['POST'])
def search_shows():
 
  search_term = request.form.get('search_term', '')
  result = db.session.query(Venue, Show).join(Show).all()
  for venue, show in result:
    print(venue.name, show.id)
    response={
    # "count": result.count(),
    "venue_name": venue.name,
    "id" : venue.id
    }

  return render_template('pages/search_shows.html', results=response, search_term=request.form.get('search_term', ''))

########################### UPDATE THE CHOSEN SHOWS ############################

@app.route('/shows/<int:venue_id>/edit', methods=['GET'])
def edit_shows(venue_id):
  form = ShowForm()
  show = Show.query.filter(Show.venue_id == venue_id).first()
  try:

    form.artist_id.data = show.artists.id
    form.venue_id.data = show.venues.id
    form.start_time.data = show.start_time
    
    print(show)
  except:
    print(sys.exc_info())
    print(show )
  finally:
    db.session.close()

  return render_template('forms/edit_show.html', form=form, show=show)

########################### SUBMIT THE UPDATE CHOSEN SHOWS ############################

@app.route('/shows/<int:venue_id>/edit', methods=['POST'])
def edit_shows_submission(venue_id):
  # take values from the form submitted, and update existing
  form = ShowForm()
  show = Show.query.filter(Show.venue_id == venue_id).first()
  show = Show.query.get(venue_id)
  try:
    
    show.artist_id = form.artist_id.data 
    show.venue_id = form.venue_id.data 
    show.start_time = form.start_time.data 

    db.session.commit()
    flash('Shows ' + form.venue_id.data   + ' was successfully Update!')
    
  except:
    flash('An error ocurred, Show ' + form.venue_id.data  + ' could not be updated')
    print(sys.exc_info())
    db.session.rollback()

  finally:
    db.session.close()

  return redirect(url_for('shows', venue_id=venue_id))

########################### DELETE THE CHOSEN SHOWS ############################

@app.route('/shows/<id>', methods=['DELETE'])
def delete_show(id):
  try:
    show =  Show.query.get(id)
    # venue.Show.clear()
    # venue_name = venue.name
    # db.session.add(venue)
    db.session.delete(show)
    db.session.commit()

    flash('Venue ' + id + ' was deleted')
  except:
    flash(' an error occured and Venue ' + id+ ' was not deleted')
    print(sys.exc_info())
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''