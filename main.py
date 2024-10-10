import mysql.connector
import random
import time
from datetime import datetime

# Global variables for player status
player_name = None
fuel = 100
speed = 300
altitude = 5000
score = 0
level = 1
max_altitude = 40000
max_speed = 600
points_per_obstacle = 50  # Points earned for avoiding an obstacle

# Establish connection to MySQL
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="2004",
            database="ProjectRamJet"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        return None

# Function to create a new player in the database
def create_player(conn, name):
    try:
        cursor = conn.cursor()
        query = "INSERT INTO player (name) VALUES (%s)"
        cursor.execute(query, (name,))
        conn.commit()
        print(f"Welcome, {name}! Your journey begins.")
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error creating player: {err}")

# Function to retrieve player status from the database
def get_player_status(conn, name):
    global fuel, speed, altitude, score, level
    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT fuel, speed, altitude, score, level FROM player WHERE name = %s"
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        if result:
            fuel, speed, altitude, score, level = result
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error retrieving player status: {err}")

# Function to update player status in the database
def update_player_status(conn, name):
    global fuel, speed, altitude, score, level
    try:
        cursor = conn.cursor()
        query = '''UPDATE player 
                   SET fuel = %s, speed = %s, altitude = %s, score = %s, level = %s
                   WHERE name = %s'''
        cursor.execute(query, (fuel, speed, altitude, score, level, name))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error updating player status: {err}")

# Function to fetch random weather conditions for a flight
def get_random_weather(conn):
    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT * FROM weather ORDER BY RAND() LIMIT 1"
        cursor.execute(query)
        weather = cursor.fetchone()
        cursor.close()

        if weather:
            print(f"\nWeather: {weather[1]} | Turbulence Level: {weather[2]}, Wind Speed: {weather[3]} mph, Temperature: {weather[4]}°C, Visibility: {weather[5]}")
            return weather
        else:
            print("No weather data found.")
            return None
    except mysql.connector.Error as err:
        print(f"Error fetching weather: {err}")
        return None

# Function to display and manage the store
def display_store(conn):
    global fuel, speed, score
    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT * FROM storeitems"
        cursor.execute(query)
        items = cursor.fetchall()
        cursor.close()

        print(f"\n--- Welcome to the Store ---")
        print(f"Your current score: {score} points.")
        for item in items:
            print(f"{item[0]}. {item[1]} - Cost: {item[2]} points, Effect: {item[3]}")

        choice = input("\nEnter the item number to purchase, or 'exit' to leave the store: ")

        if choice != 'exit':
            item_id = int(choice)
            cursor = conn.cursor(buffered=True)
            query = "SELECT * FROM storeitems WHERE id = %s"
            cursor.execute(query, (item_id,))
            item = cursor.fetchone()

            if score >= item[2]:
                score -= item[2]
                print(f"You purchased {item[1]}! {item[3]}")
                apply_item_effect(item)
                update_player_status(conn, player_name)
                log_purchased_item(conn, player_name, item_id)
            else:
                print("You don't have enough points!")
            cursor.close()
    except mysql.connector.Error as err:
        print(f"Error displaying store: {err}")

# Function to apply the item effect
def apply_item_effect(item):
    global fuel, speed, altitude
    if 'fuel' in item[3]:
        fuel += 15
    elif 'speed' in item[3]:
        speed += 50
    elif 'altitude' in item[3]:
        altitude += 2000

# Function to introduce random obstacles during flight
def avoid_obstacles():
    obstacles = ['Birds', 'Storm', 'Turbulence', 'Fog']
    if random.randint(1, 5) == 1:  # 1 in 5 chance of encountering an obstacle
        obstacle = random.choice(obstacles)
        print(f"\nObstacle: {obstacle}! Reduce speed!")
        action = input("Choose action (1. Avoid obstacle, 2. Continue): ")
        
        if action == '1':
            print(f"You successfully avoided the {obstacle}! Earned {points_per_obstacle} points.")
            return points_per_obstacle  # Earn points for avoiding the obstacle
        else:
            print(f"You hit the {obstacle}! Fuel or speed reduced.")
            return -10  # Penalty if the obstacle is not avoided
    return 0  # No obstacle encountered

# Function to log flight details
def log_flight(conn, player_name, weather_id, duration, distance, fuel_used, final_altitude, score):
    try:
        cursor = conn.cursor(buffered=True)
        query = '''INSERT INTO flightlogs (player_id, weather_id, duration, distance_traveled, fuel_used, final_altitude, score)
                   VALUES ((SELECT id FROM player WHERE name = %s LIMIT 1), %s, %s, %s, %s, %s, %s)'''
        cursor.execute(query, (player_name, weather_id, duration, distance, fuel_used, final_altitude, score))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error logging flight: {err}")

# Main function to start the flight simulation
def start_flight(conn):
    global fuel, speed, altitude, score
    print(f"\nStarting flight for {player_name}. Current fuel: {fuel}%, speed: {speed} mph, altitude: {altitude} ft.")

    # Select random weather
    weather = get_random_weather(conn)
    if weather:
        weather_id = weather[0]

        # Track flight details
        start_time = time.time()
        distance_traveled = 0

        while fuel > 0:
            print(f"\nAltitude: {altitude} ft, Speed: {speed} mph, Fuel: {fuel:.2f}%")
            print(f"Current score: {score} points.")

            action = input(f"Choose action (1. Increase Altitude, 2. Decrease Altitude, 3. Increase Speed, 4. Decrease Speed, 5. Store): ")

            if action == '1' and altitude < max_altitude:
                altitude += 1000
                print("You increased altitude.")
            elif action == '2' and altitude > 0:
                altitude -= 1000
                print("You decreased altitude.")
            elif action == '3' and speed < max_speed:
                speed += 50
                print("You increased speed.")
            elif action == '4' and speed > 0:
                speed -= 50
                print("You decreased speed.")
            elif action == '5':
                display_store(conn)

            # Simulate faster fuel consumption
            fuel -= (speed / 800) * 1.5  # Increased fuel consumption
            distance_traveled += speed / 60  # Increment distance based on speed

            # Check for obstacles and update score
            obstacle_points = avoid_obstacles()
            score += obstacle_points  # Add points for avoiding obstacles
            if obstacle_points < 0:
                fuel -= 10  # Fuel penalty if the player hits an obstacle

            # Update player status in the database
            update_player_status(conn, player_name)

            time.sleep(1)

        duration = int(time.time() - start_time) // 60
        log_flight(conn, player_name, weather_id, duration, distance_traveled, 100 - fuel, altitude, score)
        print("\nGame Over! You've run out of fuel.")
        print(f"Final score: {score} points.")
    else:
        print("Flight could not be started due to missing weather data.")

# Main entry point
def main():
    global player_name
    conn = connect_to_db()

    if conn:
        # Ask for player name
        player_name = input("Enter your player name: ")
        create_player(conn, player_name)
        get_player_status(conn, player_name)

        # Start the flight simulation
        start_flight(conn)
    else:
        print("Failed to connect to the database. Exiting...")

if __name__ == "__main__":
    main()

