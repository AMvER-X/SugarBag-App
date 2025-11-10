from flask import render_template, redirect, url_for, flash, request, jsonify, session
from app import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from models import User, Trail,  Volunteer, Admin, Customer, Challenge
from forms import SignUpForm, LoginForm, ForgotPasswordForm
import json, random
from datetime import datetime

#-------------------------------------------------------------------------------
#------------------------ LANDING PAGE ROUTES ----------------------------------
#-------------------------------------------------------------------------------

def redirect_based_on_role():
    if current_user.role == 'customer':
        return redirect(url_for('customer_dashboard'))  # Redirect to customer dashboard
    elif current_user.role == 'volunteer':
        return redirect(url_for('volunteer_dashboard'))  # Redirect to volunteer dashboard
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard
    else:
        flash("Role not recognized.", "danger")
        return redirect(url_for('home'))

    
@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect_based_on_role()  # Call a helper function for role-based redirection
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect_based_on_role()  # Redirect based on role after login
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('landing.html', form=form)


#-------------------------------------------------------------------------------
#------------------------- CUSTOMER ROUTES -------------------------------------- 
#-------------------------------------------------------------------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('customer_dashboard'))
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data, password=hashed_password, role='customer')  # default role
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('signup.html', form=form)




@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        # Here you would add logic to send a password reset email
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('home'))
    return render_template('customer/forgot_password.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        flash("You do not have access to this page.", "danger")
        return redirect(url_for('home'))

    # Pass `current_user` directly to the Challenge instance
    challenge = Challenge(customer=current_user)

    # Proceed with your logic
    #answer = request.form.get('answer', None)
    answer = True
    if answer:
        if challenge.ride_challenge_status(answer):
            flash('Challenge completed!', 'success')
        else:
            flash('Challenge in progress...', 'info')

        # This just needs to be added to the home page to show the user which trail they need to go on
        print(challenge.unpopular_trail.name)
    TrailName = challenge.unpopular_trail.name
    leaderboard = challenge.top_50_leaderboard()

    # Create a new LoginForm instance
    form = LoginForm()

    return render_template('customer/index.html', form=form, leaderboard=leaderboard, TrailName=TrailName )


@app.route('/updateLocation', methods=['POST'])
@login_required
def update_location():
    data = request.get_json()
    current_user.latitude = data.get('latitude')
    current_user.longitude = data.get('longitude')
    
    # Load the current user's active challenge
    challenge = Challenge(customer=current_user)

    # Check if the user has completed the challenge path
    challenge_complete = challenge.ride_challenge_status(answer=True)  # `answer=True` to assume challenge accepted
    

    if challenge_complete:
        # Update the user's points by 10 and save to database
        current_user.current_points += 10
        db.session.commit()
        
        return jsonify(status='complete', new_points=current_user.current_points)
    
    return jsonify(status='in_progress')

#FIGURE OUT HOW TO DISPLAY PATH OF TRAILS USER NEEDS TO TRANSVERSE ON WEBSITE PROBABLY AS A TEXT LIST


#---------------------------VOLUNTEER ROUTES--------------------------------------#
#-----------------------------------------------------------------------------#

@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer_login():
    if current_user.is_authenticated:
        return redirect(url_for('volunteer_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='volunteer').first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('volunteer_dashboard'))  # Redirect to dashboard
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('volunteer/login.html', form=form)


@app.route('/volunteer/dashboard', methods=['GET', 'POST'])
@login_required
def volunteer_dashboard():
    if current_user.role != 'volunteer':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('volunteer_login'))
    
    if request.method == 'POST':
        # Get volunteer input from the form (only when POST request is made)
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # Ensure the data is valid (you can add more validation here)
        if day and start_time and end_time:
            try:
                # Convert time strings to datetime objects
                start_time = datetime.strptime(start_time, '%H:%M').time()  # Convert to time
                end_time = datetime.strptime(end_time, '%H:%M').time()  # Convert to time

                # Explicitly convert 'day' to string to ensure it's stored as a string
                day = str(day).strip()  # Convert to string and remove any unnecessary spaces

                # Used to specify availability for volunteers
                current_user.add_availability(day, start_time, end_time)
                flash('Availability updated successfully!', 'success')
            except ValueError:
                flash('Invalid time format. Please use the correct format (HH:MM).', 'danger')
        else:
            flash('Please provide valid input for all fields.', 'danger')
    
    # Call the method to get the assigned jobs
    assigned_jobs = current_user.view_assigned_jobs() #if isinstance(current_user, Volunteer) else []

    return render_template('volunteer/dashboard.html', assigned_jobs=assigned_jobs)

# @app.route('/volunteer/mark_complete/<int:assignment_id>', methods=['POST'])
# @login_required
# def volunteer_mark_complete(assignment_id):
#     assignment = TrailAssignment.query.get_or_404(assignment_id)
#     if assignment.user_id != current_user.id or current_user.role != 'volunteer':
#         flash('Unauthorized action.', 'danger')
#         return redirect(url_for('volunteer_dashboard'))
    
#     assignment.status = 'completed'
#     db.session.commit()
#     flash("Task marked as completed!", "success")
#     return redirect(url_for('volunteer_dashboard'))


#---------------------------ADMIN ROUTES--------------------------------------#
#-----------------------------------------------------------------------------#
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard after login
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='admin').first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('admin/login.html', form=form)

@app.route('/admin-dashboard')
@login_required
def admin_dashboard():
    # Ensure only admin users can access this route
    if current_user.role != 'admin':
        flash('Access Denied. Admins only.', 'danger')
        return redirect(url_for('admin_login'))
    
    trails = Trail.query.all()
    
    # Add logic to display data or statistics relevant to admin users
    return render_template('admin/dashboard.html', user=current_user, trails=trails)

# USER MANAGEMENT

@app.route('/manage-users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access Denied. Admins only.', 'danger')
        return redirect(url_for('login'))
    
    users = User.query.all()  # Fetch all users from the database
    return render_template('admin/manage_users.html', users=users)

# Route to add a new user
@app.route('/admin/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']  # You may want to hash this

        new_user = User(email=email, role=role, password=password)  # Hash password before saving in a real app
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('manage_users'))

    return render_template('admin/add_user.html')

# Route to edit a user
@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))

    return render_template('admin/edit_user.html', user=user)


# Route to delete a user
@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('manage_users'))

#--------------------------------------------------------------------
#-----------MANAGE TRAILS-------------------------------------------
#--------------------------------------------------------------------
@app.route('/admin/manage_trails')
def manage_trails():
    red_trails = Trail.query.filter_by(status='red').all()
    yellow_trails = Trail.query.filter_by(status='yellow').all()
    #staff_volunteers = User.query.filter(User.role.in_(['staff', 'volunteer'])).all()

    return render_template('admin/manage_trails.html', red_trails=red_trails, yellow_trails=yellow_trails) #staff_volunteers=staff_volunteers to be added



@app.route('/admin/assign_maintenance/<int:trail_id>', methods=['GET', 'POST'])
def assign_maintenance(trail_id):
    trail = Trail.query.get_or_404(trail_id)
    available_volunteers = []

    if request.method == 'POST':
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        day_str = str(day).strip()

        try:
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            flash("Invalid time format. Please enter time in HH:MM format.", "danger")
            return redirect(url_for('assign_maintenance', trail_id=trail_id))

        if day and start_time and end_time:
            # Availability check as before
            available_volunteers = current_user.list_available_volunteers(day_str, start_time_obj, end_time_obj)

            if 'assign_maintenance' in request.form:
                volunteer_id = request.form.get('volunteer_id')
                # volunteer_id = 3
                print("volunteer_id from form:", volunteer_id)
                # Trail.query.filter(Trail.status == TrailStatus.RED).with_entities(Trail.id, Trail.name).all()
                
                vn = User.query.filter_by(email=volunteer_id).first()
                if vn:
                    user_id = vn.id
                
                if user_id:  # Ensure volunteer_id is not empty
                    volunteer = User.query.get(user_id)
                    if volunteer:
                        # Proceed with booking the volunteer
                        if current_user.book_volunteers(day_str, start_time, end_time, volunteer.id, trail.name):
                            db.session.commit()
                            flash(f"{volunteer.email} assigned successfully to {trail.name}!", "success")
                            return redirect(url_for('assign_maintenance', trail_id=trail_id))
                        else:
                            flash("Failed to assign volunteer.", "danger")
                    else:
                        flash("Invalid volunteer selected.", "danger")
                else:
                    flash("Please select a volunteer.", "danger")

            elif 'complete_maintenance' in request.form:
                # Complete maintenance logic
                current_user.complete_maintenance(day_str, start_time, end_time, trail.name)
                trail.status = 'green'
                db.session.commit()
                flash(f"Maintenance completed on {trail.name}. Trail status set to green.", "success")
                return redirect(url_for('manage_trails'))

    return render_template('admin/assign_maintenance.html', trail=trail, available_volunteers=available_volunteers)









# @app.route('/admin/mark_maintenance_complete/<int:assignment_id>', methods=['POST'])
# def mark_maintenance_complete(assignment_id):
#     assignment = TrailAssignment.query.get_or_404(assignment_id)
#     assignment.status = 'completed'
#     db.session.commit()
#     flash("Trail marked as maintained!", "success")
#     return redirect(url_for('manage_trails'))

# TRAILS PANEL 

@app.route('/trails/data')
def get_trail_data():
    trails = Trail.query.all()
    features = []

    for trail in trails:
        feature = {
            "type": "Feature",
            "properties": {
                "name": trail.name,
                "difficulty": trail.difficulty,
                "color": trail.status  # Assuming 'status' holds the color. Adjust if necessary.
            },
            "geometry": {
                "type": "LineString",
                "coordinates": json.loads(trail.path)  # Ensure 'path' is in JSON format.
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return jsonify(geojson)

@app.route('/update-trail-status', methods=['POST'])
def update_trail_status():
    trail_id = request.json.get('id')
    new_status = request.json.get('status')

    trail = Trail.query.get(trail_id)
    if trail:
        trail.status = new_status
        db.session.commit()
        return jsonify({"success": True, "message": "Trail status updated successfully!"})
    else:
        return jsonify({"success": False, "message": "Trail not found."})