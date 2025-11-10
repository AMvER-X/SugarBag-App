from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from app import db, login_manager
from datetime import datetime
from enum import Enum
import networkx as nx
from werkzeug.security import generate_password_hash, check_password_hash
import json, math



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#-----------------------------------------------------------------------------
#--------------------------USER CLASS-----------------------------------------
#-----------------------------------------------------------------------------

class UserRole(Enum):
    CUSTOMER = 'customer'
    STAFF = 'staff'
    VOLUNTEER = 'volunteer'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin', 'volunteer', 'customer''
    
    
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }

    def set_password(self, password):
        self.password = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password, password)

#------------------------------------------------------------------------------
#-----------------------ADMIN CLASS--------------------------------------------
#------------------------------------------------------------------------------
class Admin(User):
    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }

    # Returns a list of trails, which need maintenance
    def red_trails(self):
        return Trail.query.filter(Trail.status == TrailStatus.RED).with_entities(Trail.id, Trail.name).all()

        # Returns a list of available workers available for booking maintenance work
    def list_available_volunteers(self, day, start_time, end_time):
        # Query to find available slots across all volunteers
        available_slots = Availability.query.filter(
            Availability.day == day,
            Availability.start_time <= start_time,  # Allow start times equal to or earlier than the requested start
            Availability.end_time >= end_time,      # Allow end times equal to or later than the requested end
            Availability.booked == False
        ).all()


        # Compile a list of available volunteers based on the availability results
        available_volunteers = []
        for slot in available_slots:
            volunteer = Volunteer.query.get(slot.volunteer_id)
            if volunteer:  # Ensure the volunteer exists
                available_volunteers.append({
                    "volunteer_id": volunteer.id,
                    "email": volunteer.email,
                    "available_start": slot.start_time,
                    "available_end": slot.end_time
                })
        
        return available_volunteers
    
    # Allows the staff members to use available volunteers for maintenance
    def book_volunteers(self, day, start_time, end_time, volunteer_id: int, trail_name: str = None):
        # Convert inputs to appropriate formats
        day_str = str(day)
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M').time()

        # Query the specific availability for the volunteer
        availability = Availability.query.filter(
            Availability.day == day_str,
            Availability.start_time <= start_time_obj,
            Availability.end_time >= end_time_obj,
            Availability.volunteer_id == volunteer_id,  # Ensure it's the correct volunteer
            Availability.booked == False
        ).first()

        if not availability:
            print(f"No available slots found for volunteer ID {volunteer_id} on day {day} from {start_time} to {end_time}.")
            return False

        # Mark the availability as booked
        availability.booked = True

        if trail_name:
                volunteer = Volunteer.query.get(volunteer_id)
                if volunteer:
                    volunteer.add_job(trail_name)

        db.session.commit()
        print(f"Volunteer {volunteer_id} successfully booked for maintenance on {trail_name}.")
        return True


    # Mark maintenance schedule as complete
    def complete_maintenance(self, day, start_time, end_time, trail_name):
        assigned_slots = Availability.query.filter_by(
            day=day,
            start_time=start_time,
            end_time=end_time,
            booked=True
        ).all()
        
        for slot in assigned_slots:
            volunteer = Volunteer.query.get(slot.volunteer_id)
            if volunteer:
                slot.booked = False
                
                # Only remove the job if it exists in the current jobs list
                if trail_name in volunteer.current_jobs:
                    volunteer.remove_job(trail_name)

        db.session.commit()


#------------------------------------------------------------------------------
#--------------------- CUSTOMER CLASS------------------------------------------
#------------------------------------------------------------------------------

class Customer(User):
    __mapper_args__ = {
        'polymorphic_identity': 'customer'
    }
    current_points = db.Column(db.Float, default=0)
    total_points = db.Column(db.Float, default=0)

    def __init__(self):
        self.latitude = 0
        self.longitude = 0

     # Validatess points value
    def validate_points(self, value):
        if value < 0:
            raise ValueError("Points cannot be negative")
        else:
            return value
        
    # Then let's them accept challenge promt
    def accept_challenge(self, answer):
        self.longitude = 0.0
        self.latitude = 0.0

        if answer:
            self.challenge_participation = True
            return True
        else:
            self.challenge_participation = False
            return False
        

    # Creates ride and assigns ride challenge to user, based on path with least number of people
    def assign_trail_difficulty(self):
        points = self.current_points
        if points <= 30:
            difficulty = 'Green'
        elif points <= 130:
            difficulty = 'Blue'
        elif points <= 500:
            difficulty = 'Black'
        else:
            difficulty = 'Double Black'
        print(difficulty)
        return difficulty
    
    # Gets users current position
    def get_user_pos(self):
        return {'latitude': self.latitude, 'longitude': self.longitude}



#--------------------------------------------------------------------------
#--------------------VOLUNTEER---------------------------------------------
#--------------------------------------------------------------------------

class Volunteer(User):
    __mapper_args__ = {
        'polymorphic_identity': 'volunteer'
    }

    current_jobs = db.Column(db.JSON, default=[])

    def add_job(self, trail_name):
        if trail_name not in (self.current_jobs or []):  # Avoid duplicates
            self.current_jobs = (self.current_jobs or []) + [trail_name]
            db.session.commit()

    def remove_job(self, trail_name):
        if trail_name in (self.current_jobs or []):
            self.current_jobs.remove(trail_name)
            db.session.commit()

    # Allows the user to specify a time slot they are available for 
    def add_availability(self, day, start_time, end_time):
        if not self.id:
            print("Volunteer ID is not set yet. Committing volunteer first.")
            db.session.add(self)
            db.session.commit()
        
        availability = Availability(volunteer_id=self.id, 
                                    day=day,
                                    start_time=start_time,
                                    end_time=end_time)
        print(f"Adding availability for volunteer with ID: {self.id}")
        
        db.session.add(availability)
        db.session.commit()

    # Allows volunteers to view all assigned jobs with details
    def view_assigned_jobs(self):
        # assigned_jobs = Availability.query.filter_by(volunteer_id=self.id, booked=True).all()
        
        # job_details = []
        # for job in assigned_jobs:
        #     for trail in job.trails:  # Accessing the associated trails
        #         job_details.append({
        #             "day": job.day,
        #             "start_time": job.start_time,
        #             "end_time": job.end_time,
        #             "trail_name": trail.name
        #         })
        jobs = Volunteer.query.with_entities(Volunteer.current_jobs).all()
        return jobs
    
# Association table for Availability and Trail
trail_volunteer_maintenance = db.Table('availability_trail',
    db.Column('availability_id', db.Integer, db.ForeignKey('availability.id'), primary_key=True),
    db.Column('trail_id', db.Integer, db.ForeignKey('trail.id'), primary_key=True)
)
    
# Class for specifying maintainence
class Availability(db.Model):
    __tablename__ = 'availability'
    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day = db.Column(db.String(10))
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    booked = db.Column(db.Boolean, default=False, nullable=False)

    # Many-to-many relationship to Trail through the association table
    trails = db.relationship('Trail', secondary='availability_trail', back_populates='availabilities')

    # Back reference to volunteer, using `users` table as the FK source
    volunteer = db.relationship('User', backref='availabilities')

    __table_args__ = {'extend_existing': True}
    
class TrailStatus(Enum):
    GREEN = 'Green'
    YELLOW = 'Yellow'
    RED = 'Red'

class TrailDifficulty(Enum):
    GREEN = 'Green'
    BLUE = 'Blue'
    Black = 'Black'
    DB = 'Double Black'


class Trail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    path = db.Column(db.Text, nullable=True)
    people_count = db.Column(db.Integer, nullable=False, default=0)

    # Many-to-many relationship to Availability through the association table
    availabilities = db.relationship('Availability', secondary=trail_volunteer_maintenance, back_populates='trails')

    


# class TrailAssignment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     trail_id = db.Column(db.Integer, db.ForeignKey('trail.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('volunteer.id'), nullable=False)
#     assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
#     status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'completed'

#     # Relationships
#     trail = db.relationship('Trail', backref=db.backref('assignments', cascade='all, delete-orphan'))
#     user = db.relationship('Volunteer', backref=db.backref('assignments', cascade='all, delete-orphan'))


#----------------------------------------------------------------
#-----------------CHALLENGE--------------------------------------
#----------------------------------------------------------------
# Association table for Challenge and Trail many-to-many relationship
challenge_trails = db.Table('challenge_trails',
    db.Column('challenge_id', db.Integer, db.ForeignKey('challenge.id'), primary_key=True),
    db.Column('trail_id', db.Integer, db.ForeignKey('trail.id'), primary_key=True)
)


class Challenge(db.Model):
    __tablename__ = 'challenge'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    point_adder = db.Column(db.Float, default=10.0)

    # Relationships
    user = db.relationship('Customer', backref='challenges')
    trails = db.relationship('Trail', secondary=challenge_trails, backref='challenges')

    def __init__(self, customer):
        self.user = customer
        self.index = 0
        self.unpopular_trail = None


    '''
    def create_trail_paths(self, target_trail):
        # Load GeoJSON data
        with open("./static/trails.geojson") as f:
            geojson_data = json.load(f)

        # Create an empty directed graph
        G = nx.DiGraph()

        # Add edges from the GeoJSON data
        for feature in geojson_data["features"]:
            coordinates = feature["geometry"]["coordinates"]
            trail_name = feature["properties"]["name"]

            # Loop through each point on the trail, adding an edge between consecutive points
            for i in range(len(coordinates) - 1):
                start = tuple(coordinates[i])      # Convert start coordinate to a tuple
                end = tuple(coordinates[i + 1])    # Convert next coordinate to a tuple

                # Add an edge between each consecutive point along the trail
                G.add_edge(start, end, name=trail_name)
                
        # Define required start points (trail names or coordinates)
        self.start_trails = ["Milky Way", "Bees Knees", "Bottom Power Line Access Track", 
                             "Sour Power", "The Drop In Clinic", "Aero"]
        

        # Find nodes associated with required trails
        required_nodes = []
        for feature in geojson_data["features"]:
            trail_name = feature["properties"]["name"]
            if trail_name in self.start_trails:
                coordinates = feature["geometry"]["coordinates"]
                start = tuple(coordinates[0])  # Start at the beginning of each trail
                required_nodes.append(start)

        # Function to find all paths that connect the specified start points
        def find_all_paths(graph, start_nodes):
            all_paths = []
            for i in range(len(start_nodes)):
                for j in range(i + 1, len(start_nodes)):
                    start = start_nodes[i]
                    end = start_nodes[j]
                    # Find all paths from start to end
                    for path in nx.all_simple_paths(graph, source=start, target=end):
                        all_paths.append(path)
            return all_paths

        # Get all paths connecting the required start points
        all_paths = find_all_paths(G, required_nodes)  # List of paths with node coordinates

        # Convert paths to trail sequences with names, only including paths that contain target_trail
        valid_paths = []
        for path in all_paths:
            trail_sequence = []
            for i in range(len(path) - 1):
                # Get the trail name from the edge connecting two consecutive points
                trail = G[path[i]][path[i + 1]]["name"]
                trail_sequence.append(trail)

            # Check if the target trail is in the trail sequence
            if target_trail in trail_sequence:
                valid_paths.append(trail_sequence)
        self.trail_path_list = valid_paths
        return valid_paths
    '''

    # Filters trail list by difficulty and status
    def filter_by_requirements(self, difficulty):
        new_trail_list = Trail.query.filter(
            Trail.difficulty == difficulty,
            Trail.status != "Red"
        ).all()
        print(new_trail_list)
        return new_trail_list
    
    # Finds least busy trail out of a list of trails
    def least_busy_trail(self, trails_list):
        if not trails_list:  # Check if the list is empty
            return None  # Or handle this case appropriately (e.g., return a default trail)
        
        min_trail = trails_list[0]
        for i in range(1, len(trails_list)):  # Start from index 1 since min_trail is initialized as trails_list[0]
            if trails_list[i].people_count < min_trail.people_count:
                min_trail = trails_list[i]
        
        return min_trail
    

    # Determines path of trails for challenge based on user's answer
    def determine_trail(self, answer):
        if self.user and self.user.accept_challenge(answer):
            difficulty = self.user.assign_trail_difficulty()
            filtered_list = self.filter_by_requirements(difficulty)
            self.unpopular_trail = self.least_busy_trail(filtered_list)
        return self.unpopular_trail
        
    # Tracks user position to ensure they are still partaking in challenge
    def ride_challenge_status(self, answer):
        if not self.user:
            print("User is None in ride_challenge_status")
            return False
        
        if not self.unpopular_trail:
            print("No trail assigned yet, determining trail.")
            self.unpopular_trail = self.determine_trail(answer)
        
        if not self.unpopular_trail or not self.unpopular_trail.path:
            print("Unpopular trail is None or has no path.")
            return False

        user_lat, user_lon = self.user.latitude, self.user.longitude

        # Ensure index is within bounds
        if self.index < len(self.unpopular_trail.path):
            try:
                trail_lat, trail_lon = self.unpopular_trail.path[self.index]
            except ValueError:
                print(f"Error unpacking coordinates at index {self.index}.")
                return False
        else:
            print("Index is out of bounds for the trail path.")
            return False

        # Calculate distance and proceed
        distance = math.sqrt((user_lat - trail_lat)**2 + (user_lon - trail_lon)**2)
        if distance < 10:
            self.index += 1  # Move to the next trail point

        if self.index >= len(self.unpopular_trail.path):
            return True  # Challenge completed

        return False  # Not yet completed


        # Returns top 50 leaderboard
    def top_50_leaderboard(self):
        return Customer.query.order_by(Customer.total_points.desc()).limit(50).all()
