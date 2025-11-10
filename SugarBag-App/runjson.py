import json
import random
from app import app, db
from models import Trail

"""
This program serves to simulate the real world IoT data devices and the data cleaning analysis we have done by calculating the number of people we have on the trails at any given
time, this will populate the trails and therefore needs to be run before anything else can work
"""

# Path to the GeoJSON file
file_path = 'static/trails.geojson'

# Read and parse the GeoJSON file within the application context
with app.app_context():
    with open(file_path, 'r') as file:
        data = json.load(file)
        features = data['features']

        for feature in features:
            properties = feature['properties']
            geometry = feature['geometry']

            if geometry['type'] == 'LineString':
                coordinates = geometry['coordinates']

                # Serialize coordinates as a string
                path = json.dumps(coordinates)

                if coordinates and isinstance(coordinates[0], list):
                    # Use the first coordinate as the representative point
                    longitude, latitude = coordinates[0]

                    # Extract relevant properties
                    name = properties.get('name', 'Unnamed Trail')
                    status = properties.get('status', 'Green')
                    difficulty = properties.get('difficulty', 'Black')

                    # Generate a random people count between 0 and 100
                    people_count = random.randint(0, 100)

                    # Create and add a new Trail object to the database
                    new_trail = Trail(
                        name=name,
                        status=status,
                        difficulty=difficulty,
                        latitude=latitude,
                        longitude=longitude,
                        path=path,  # Save the serialized path
                        people_count=people_count  # Add the random people count
                    )
                    db.session.add(new_trail)
                else:
                    print(f"Invalid coordinate format for feature: {properties.get('name', 'Unnamed Trail')}")

        # Commit all the changes to the database
        db.session.commit()

    print("Trails have been added to the database with random people counts.")
