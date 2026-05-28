from flask import Flask, render_template, request, redirect, session, flash, jsonify
import mysql.connector
import random
import urllib.request
import json
import requests
from amadeus import Client, ResponseError
from datetime import datetime, timedelta
from decimal import Decimal
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- API KEYS ---ṇ
RAPID_API_KEY = "fc26678b2emsh10727542d487282p106a2cjsn4c5c6c02d11d"

amadeus = Client(
    client_id="o6SrVC9Y06rJ2ObIfAYwT73cTYjiNVSb",
    client_secret="91ANNPRlIfKKCPN5"
)

# --- RAPIDAPI HOSTS ---
TRAIN_API_HOST = "irctc1.p.rapidapi.com"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="route@12r",
        database="travel_planner"
    )

# --- CITY COORDINATES FOR DISTANCE LOGIC ---
CITY_COORDINATES = {
    "DEL": (28.6139, 77.2090), "DELHI": (28.6139, 77.2090),
    "BOM": (19.0760, 72.8777), "MUMBAI": (19.0760, 72.8777),
    "BLR": (12.9716, 77.5946), "BANGALORE": (12.9716, 77.5946), "BENGALURU": (12.9716, 77.5946),
    "MAA": (13.0827, 80.2707), "CHENNAI": (13.0827, 80.2707),
    "HYD": (17.3850, 78.4867), "HYDERABAD": (17.3850, 78.4867),
    "CCU": (22.5726, 88.3639), "KOLKATA": (22.5726, 88.3639),
    "AMD": (23.0225, 72.5714), "AHMEDABAD": (23.0225, 72.5714),
    "PNQ": (18.5204, 73.8567), "PUNE": (18.5204, 73.8567),
    "JAI": (26.9124, 75.7873), "JAIPUR": (26.9124, 75.7873),
    "LKO": (26.8467, 80.9462), "LUCKNOW": (26.8467, 80.9462),
    "COK": (9.9312, 76.2673), "KOCHI": (9.9312, 76.2673),
    "GOI": (15.2993, 74.1240), "GOA": (15.2993, 74.1240),
    "PAT": (25.5941, 85.1376), "PATNA": (25.5941, 85.1376),
    "GAU": (26.1445, 91.7362), "GUWAHATI": (26.1445, 91.7362),
    "IXC": (30.7333, 76.7794), "CHANDIGARH": (30.7333, 76.7794),
    "SXR": (34.0837, 74.7973), "SRINAGAR": (34.0837, 74.7973),
    "ATQ": (31.6340, 74.8723), "AMRITSAR": (31.6340, 74.8723),
    "VNS": (25.3176, 82.9739), "VARANASI": (25.3176, 82.9739),
    "BBI": (20.2961, 85.8245), "BHUBANESWAR": (20.2961, 85.8245),
    "IXR": (23.3441, 85.3096), "RANCHI": (23.3441, 85.3096),
    "RPR": (21.2514, 81.6296), "RAIPUR": (21.2514, 81.6296),
    "IDR": (22.7196, 75.8577), "INDORE": (22.7196, 75.8577),
    "BHO": (23.2599, 77.4126), "BHOPAL": (23.2599, 77.4126),
    "NAG": (21.1458, 79.0882), "NAGPUR": (21.1458, 79.0882),
    "TRV": (8.5241, 76.9366), "THIRUVANANTHAPURAM": (8.5241, 76.9366),
    "IXM": (9.9252, 78.1198), "MADURAI": (9.9252, 78.1198),
    "CJB": (11.0168, 76.9558), "COIMBATORE": (11.0168, 76.9558),
    "VTZ": (17.6868, 83.2185), "VISAKHAPATNAM": (17.6868, 83.2185),
    # --- COMMON INDIAN RAILWAY STATION CODES ---
    "NDLS": (28.6139, 77.2090), "DLI": (28.6139, 77.2090), "NZM": (28.6139, 77.2090), # Delhi
    "BCT": (19.0760, 72.8777), "BDTS": (19.0760, 72.8777), "CSMT": (19.0760, 72.8777), # Mumbai
    "MAS": (13.0827, 80.2707), "MS": (13.0827, 80.2707), # Chennai
    "SBC": (12.9716, 77.5946), "YPR": (12.9716, 77.5946), "KSR": (12.9716, 77.5946), # Bangalore
    "HWH": (22.5726, 88.3639), "SDAH": (22.5726, 88.3639), # Kolkata
    "HYB": (17.3850, 78.4867), "SC": (17.3850, 78.4867), # Hyderabad
    "ADI": (23.0225, 72.5714), # Ahmedabad
    "PNBE": (25.5941, 85.1376), # Patna
    "GHY": (26.1445, 91.7362), # Guwahati
    "LKO": (26.8467, 80.9462), "LJN": (26.8467, 80.9462), # Lucknow
    "JAI": (26.9124, 75.7873), "JP": (26.9124, 75.7873), # Jaipur
    "PNQ": (18.5204, 73.8567), "PUNE": (18.5204, 73.8567), # Pune
    "VNS": (25.3176, 82.9739), "BSB": (25.3176, 82.9739), # Varanasi
    "IXC": (30.7333, 76.7794), "CDG": (30.7333, 76.7794), # Chandigarh
    "SXR": (34.0837, 74.7973), # Srinagar
    "ATQ": (31.6340, 74.8723), "ASR": (31.6340, 74.8723), # Amritsar
    "BBI": (20.2961, 85.8245), "BBS": (20.2961, 85.8245), # Bhubaneswar
    "IXR": (23.3441, 85.3096), "RNC": (23.3441, 85.3096), # Ranchi
    "RPR": (21.2514, 81.6296), # Raipur
    "IDR": (22.7196, 75.8577), "INDB": (22.7196, 75.8577), # Indore
    "BHO": (23.2599, 77.4126), "BPL": (23.2599, 77.4126), "BHOPAL": (23.2599, 77.4126), # Bhopal
    "UJN": (23.1765, 75.7885), "UJJAIN": (23.1765, 75.7885), # Ujjain
    "NAG": (21.1458, 79.0882), "NGP": (21.1458, 79.0882), # Nagpur
    "GWL": (26.2124, 78.1772), "GWALIOR": (26.2124, 78.1772), # Gwalior
    "JBP": (23.1815, 79.9864), "JABALPUR": (23.1815, 79.9864), # Jabalpur
    "RTM": (23.3315, 75.0367), "RATLAM": (23.3315, 75.0367), # Ratlam
    "KOTA": (25.2138, 75.8648), # Kota
    "AGC": (27.1767, 78.0081), "AGRA": (27.1767, 78.0081), # Agra
    "MTJ": (27.4924, 77.6737), "MATHURA": (27.4924, 77.6737), # Mathura
    "CNB": (26.4499, 80.3319), "KANPUR": (26.4499, 80.3319), # Kanpur
    "ALD": (25.4358, 81.8463), "PRYJ": (25.4358, 81.8463), "ALLAHABAD": (25.4358, 81.8463), # Prayagraj
    "DDU": (25.2757, 83.1203), "MGS": (25.2757, 83.1203), # Pt Deen Dayal Upadhyaya / Mughalsarai
    "GKP": (26.7606, 83.3731), "GORAKHPUR": (26.7606, 83.3731), # Gorakhpur
    "SUR": (17.6599, 75.9064), "SOLAPUR": (17.6599, 75.9064), # Solapur
    "VAK": (19.8762, 75.3433), "AURANGABAD": (19.8762, 75.3433), # Aurangabad
    # --- INTERNATIONAL HUBS ---
    "DXB": (25.2532, 55.3657), "DUBAI": (25.2532, 55.3657),
    "DOH": (25.2731, 51.6082), "DOHA": (25.2731, 51.6082),
    "LHR": (51.4700, -0.4543), "LONDON": (51.4700, -0.4543),
    "JFK": (40.6413, -73.7781), "NEW YORK": (40.6413, -73.7781),
    "SIN": (1.3644, 103.9915), "SINGAPORE": (1.3644, 103.9915),
    "BKK": (13.6900, 100.7501), "BANGKOK": (13.6900, 100.7501),
    "CDG": (49.0097, 2.5479), "PARIS": (49.0097, 2.5479),
    "FRA": (50.0379, 8.5622), "FRANKFURT": (50.0379, 8.5622),
    "IST": (41.2753, 28.7519), "ISTANBUL": (41.2753, 28.7519),
    "ZRH": (47.4582, 8.5555), "ZURICH": (47.4582, 8.5555),
    "AUH": (24.4330, 54.6511), "ABU DHABI": (24.4330, 54.6511),
    "HND": (35.5494, 139.7798), "NRT": (35.7720, 140.3929), "TOKYO": (35.5494, 139.7798),
    "SYD": (-33.9399, 151.1753), "SYDNEY": (-33.9399, 151.1753),
    "SFO": (37.6189, -122.3750), "SAN FRANCISCO": (37.6189, -122.3750),
    "LAX": (33.9416, -118.4085), "LOS ANGELES": (33.9416, -118.4085),
    "YYZ": (43.6777, -79.6248), "TORONTO": (43.6777, -79.6248),
    "MEL": (-37.6690, 144.8410), "MELBOURNE": (-37.6690, 144.8410),
    "HKG": (22.3080, 113.9185), "HONG KONG": (22.3080, 113.9185),
    "KUL": (2.7456, 101.7072), "KUALA LUMPUR": (2.7456, 101.7072),
    "CMB": (7.1811, 79.8837), "COLOMBO": (7.1811, 79.8837),
    "MLE": (4.1919, 73.5291), "MALE": (4.1919, 73.5291),
    "SGN": (10.8185, 106.6588), "HO CHI MINH": (10.8185, 106.6588),
    "ICN": (37.4602, 126.4407), "SEOUL": (37.4602, 126.4407),
    "PEK": (40.0799, 116.6031), "BEIJING": (40.0799, 116.6031),
    "PVG": (31.1443, 121.8083), "SHANGHAI": (31.1443, 121.8083),
}

def calculate_distance(city1, city2):
    """Calculates distance between two cities using Haversine formula"""
    import math
    c1 = CITY_COORDINATES.get(city1.upper())
    c2 = CITY_COORDINATES.get(city2.upper())
    
    if not c1 or not c2:
        # Detect if international route based on known hub list or length of names
        hubs = ["DXB", "DOH", "LHR", "JFK", "SIN", "BKK", "CDG", "FRA", "IST", "ZRH", "AUH", "HND", "SYD", "SFO", "LAX", "YYZ", "HKG"]
        if city1.upper() in hubs or city2.upper() in hubs or len(city1) > 8 or len(city2) > 8:
            return random.randint(4500, 12000) # International range
        return random.randint(150, 800) # Domestic range
    
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c # Earth radius in KM
    return distance

def format_datetime(dt_string):
    dt = datetime.fromisoformat(dt_string)
    return dt.strftime("%d %b %Y | %H:%M")

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user:
        session['user'] = username
        return redirect('/home')
    else:
        flash("Invalid username or password")
        return redirect('/')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        flash("Passwords do not match")
        return redirect('/')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash("Already registered! Please log in")
        cursor.close()
        db.close()
        return redirect('/')

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, password)
    )
    cursor.execute(
        "INSERT INTO wallet (username, balance) VALUES (%s, %s)",
        (username, 10000)
    )
    db.commit()
    cursor.close()
    db.close()

    session['user'] = username
    return redirect('/home')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/my-bookings')
def my_bookings():
    if 'user' not in session:
        return redirect('/')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM bookings WHERE username=%s ORDER BY id DESC", (session['user'],))
    bookings = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("my_bookings.html", bookings=bookings)

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT balance FROM wallet WHERE username=%s", (session['user'],))
    wallet = cursor.fetchone()

    cursor.close()
    db.close()

    balance = wallet['balance'] if wallet else 0

    return render_template('home.html', balance=balance)

@app.route('/wallet')
def wallet():
    if 'user' not in session:
        return redirect('/')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT balance FROM wallet WHERE username=%s", (session['user'],))
    wallet_data = cursor.fetchone()

    cursor.close()
    db.close()

    balance = wallet_data['balance'] if wallet_data else 0

    return render_template("wallet.html", balance=balance)

@app.route('/flights-search')
def flights_search():
    if 'user' not in session:
        return redirect('/')
    return render_template('flights_search.html')

@app.route('/search-flights', methods=['POST'])
def search_flights():
    if 'user' not in session:
        return redirect('/')

    from_city = request.form['from_city'].strip().upper()
    to_city = request.form['to_city'].strip().upper()
    date = request.form['date']

    # Using Mock Data instead of real API
    flights = get_flights_mock_data(from_city, to_city, date)
    no_match = len(flights) == 0

    return render_template(
        "flights_results.html",
        from_city=from_city,
        to_city=to_city,
        flights=flights,
        no_match=no_match,
        api_error=None
    )

def get_flights_mock_data(from_city, to_city, date):
    """Generates realistic flight mock data based on distance"""
    flights = []
    airlines = [
        {"name": "IndiGo", "code": "6E", "type": "Domestic"},
        {"name": "Air India", "code": "AI", "type": "Both"},
        {"name": "Vistara", "code": "UK", "type": "Both"},
        {"name": "SpiceJet", "code": "SG", "type": "Domestic"},
        {"name": "Akasa Air", "code": "QP", "type": "Domestic"},
        {"name": "Qatar Airways", "code": "QR", "type": "International"},
        {"name": "Emirates", "code": "EK", "type": "International"},
        {"name": "Etihad Airways", "code": "EY", "type": "International"},
        {"name": "Turkish Airlines", "code": "TK", "type": "International"},
        {"name": "Swiss International", "code": "LX", "type": "International"},
        {"name": "Singapore Airlines", "code": "SQ", "type": "International"},
        {"name": "Lufthansa", "code": "LH", "type": "International"},
        {"name": "British Airways", "code": "BA", "type": "International"},
        {"name": "Air France", "code": "AF", "type": "International"},
        {"name": "Finnair", "code": "AY", "type": "International"},
        {"name": "KLM", "code": "KL", "type": "International"},
        {"name": "Japan Airlines", "code": "JL", "type": "International"},
        {"name": "Cathay Pacific", "code": "CX", "type": "International"}
    ]
    
    distance = calculate_distance(from_city, to_city)
    is_international = distance > 3500 or from_city in ["DXB", "DOH", "LHR", "JFK", "SIN", "BKK", "CDG", "FRA", "IST", "ZRH", "AUH", "HND"] or to_city in ["DXB", "DOH", "LHR", "JFK", "SIN", "BKK", "CDG", "FRA", "IST", "ZRH", "AUH", "HND"]
    
    # Filter airlines based on route
    if is_international:
        available_airlines = [a for a in airlines if a["type"] in ["International", "Both"]]
    else:
        available_airlines = [a for a in airlines if a["type"] in ["Domestic", "Both"]]
    
    # Flight duration: ~45 mins for takeoff/landing + distance/820 km/h
    standard_dur_mins = 45 + (distance / 820) * 60
    
    # Price logic: 
    if is_international:
        # International: Base 12000 + Distance * 6.8 (Approx ₹60k for 7k km)
        standard_base_price = 12000 + (distance * 6.8)
    else:
        # Domestic: Base 1800 + Distance * 3.8 (Approx ₹6k for 1.1k km)
        standard_base_price = 1800 + (distance * 3.8)
    
    for i in range(random.randint(8, 16)):
        airline = random.choice(available_airlines)
        flight_no = f"{airline['code']} {random.randint(100, 9999)}"
        
        dep_h = random.randint(0, 23)
        dep_m = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
        departure_dt = f"{date}T{dep_h:02d}:{dep_m:02d}:00"
        
        dep_obj = datetime.fromisoformat(departure_dt)
        # Randomize duration slightly (+/- 5-10% or fixed mins)
        actual_dur = standard_dur_mins + random.randint(-10, 20)
        arr_obj = dep_obj + timedelta(minutes=actual_dur)
        arrival_dt = arr_obj.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Skip flights that have already departed if date is today
        if dep_obj < datetime.now():
            continue
            
        price = int(standard_base_price + random.randint(-400, 1200))
        dur_str = f"{int(actual_dur//60)}h {int(actual_dur%60)}m"
        
        banks = ["Axis Bank", "HDFC Bank", "ICICI Bank", "SBI", "Kotak Bank", "CitiBank"]
        
        flights.append({
            "airline": airline['name'],
            "flight_no": flight_no,
            "carrierCode": airline['code'],
            "number": flight_no.split()[1],
            "from": from_city,
            "to": to_city,
            "departure_display": format_datetime(departure_dt),
            "arrival_display": format_datetime(arrival_dt),
            "departure_raw": departure_dt,
            "arrival_raw": arrival_dt,
            "status": "Available",
            "price": price,
            "price_total": str(price),
            "currency": "INR",
            "within_two_hours": (dep_obj - datetime.now()) <= timedelta(hours=2),
            "duration": dur_str,
            "duration_iso": f"PT{int(actual_dur//60)}H{int(actual_dur%60)}M",
            "stops": "Non-Stop" if distance < 2500 else "1 Stop",
            "rating": round(random.uniform(4.0, 4.9) if airline['type'] == "International" else random.uniform(3.8, 4.7), 1),
            "reviews": random.randint(500, 10000),
            "promo_bank": random.choice(banks),
            "promo_amount": random.randint(500, 3500) if is_international else random.randint(500, 1500),
            "cabin": random.choice(["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS"]) if is_international else "ECONOMY"
        })
    
    flights.sort(key=lambda x: x["departure_raw"])
    return flights

@app.route('/trains')
def trains():
    if 'user' not in session:
        return redirect('/')
    return render_template('trains_search.html')

@app.route('/buses')
def buses():
    if 'user' not in session:
        return redirect('/')
    return render_template('buses_search.html')

# ==========================================
# REST APIs for Trains and Buses (Compulsory)
# ==========================================
def get_trains_api_data(org, dest, dt):
    """Generates realistic mock data for Indian Railways based on distance"""
    trains = []
    
    train_types = [
        {"name": "Rajdhani Express", "price_mult": 2.2, "speed": 90},
        {"name": "Shatabdi Express", "price_mult": 2.0, "speed": 85},
        {"name": "Duronto Express", "price_mult": 1.7, "speed": 80},
        {"name": "Humsafar Express", "price_mult": 1.5, "speed": 75},
        {"name": "Garib Rath", "price_mult": 1.0, "speed": 70},
        {"name": "Jan Shatabdi", "price_mult": 1.1, "speed": 75},
        {"name": "Vande Bharat", "price_mult": 2.5, "speed": 110},
        {"name": "Express", "price_mult": 0.8, "speed": 60}
    ]
    
    classes = ["1A", "2A", "3A", "SL"]
    distance = calculate_distance(org, dest)
    
    for _ in range(random.randint(8, 14)):
        t_type = random.choice(train_types)
        train_no = str(random.randint(12000, 22999))
        
        dep_h = random.randint(0, 23)
        dep_m = random.choice([0, 15, 30, 45])
        departure_dt = f"{dt}T{dep_h:02d}:{dep_m:02d}:00"
        
        # Duration: Distance / Speed + smaller random buffer for stops
        standard_dur_hours = distance / t_type["speed"]
        total_dur_mins = (standard_dur_hours * 60) + random.randint(15, 60)
        
        dep_obj = datetime.fromisoformat(departure_dt)
        # Skip past trains if date is today
        if dep_obj < datetime.now():
            continue
            
        arr_obj = dep_obj + timedelta(minutes=total_dur_mins)
        arrival_dt = arr_obj.strftime("%Y-%m-%dT%H:%M:%S")
        
        selected_class = random.choice(classes)
        # Price: Base 120 + Distance * 0.85 (Approx ₹1100 base for Delhi-Mumbai)
        standard_base_price = (120 + (distance * 0.85)) * t_type["price_mult"]
        class_mult = {"1A": 3.2, "2A": 2.2, "3A": 1.5, "SL": 0.6}
        final_price = int(standard_base_price * class_mult[selected_class])
        
        trains.append({
            "operator": t_type["name"],
            "train_name": t_type["name"],
            "train_no": train_no,
            "train_number": train_no,
            "from": org.upper(),
            "to": dest.upper(),
            "from_station_name": org.upper(),
            "to_station_name": dest.upper(),
            "departure": departure_dt,
            "arrival": arrival_dt,
            "from_std": departure_dt.split('T')[1],
            "to_sta": arrival_dt.split('T')[1],
            "price": final_price,
            "class": selected_class,
            "status": "Available",
            "seats_available": random.randint(5, 120),
            "duration": f"{int(total_dur_mins//60)}h {int(total_dur_mins%60)}m",
            "run_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "classes": classes
        })
    
    trains.sort(key=lambda x: x["departure"])
    return trains

def get_buses_api_data(source, dest, dt_str):
    """Generates realistic mock data for Bus operators based on distance"""
    buses = []
    operators = [
        "Zingbus", "IntrCity SmartBus", "SRS Travels", 
        "VRL Travels", "Orange Travels", "National Travels", 
        "Sharma Transports", "Paulo Travels", "BigBus"
    ]
    
    bus_types = [
        "Volvo A/C Sleeper (2+1)", "BharatBenz A/C Sleeper (2+1)",
        "Scania A/C Multi-Axle Semi Sleeper", "Non-A/C Sleeper (2+1)",
        "A/C Seater (2+2)", "Electric A/C Sleeper"
    ]

    source_clean = source.strip().upper()
    dest_clean = dest.strip().upper()
    
    if source_clean == dest_clean:
        return []

    distance = calculate_distance(source_clean, dest_clean)
    
    # Bus speed: ~48 km/h average
    standard_dur_hours = distance / 48
    num_results = random.randint(15, 25) if distance < 600 else random.randint(5, 10)

    for _ in range(num_results):
        try:
            dt = datetime.fromisoformat(dt_str)
        except:
            dt = datetime.now()
        
        # Randomize duration slightly
        dur_hours = standard_dur_hours + random.uniform(-0.5, 1.5)
        if dur_hours < 1: dur_hours = 1
        dur_mins = random.choice([0, 15, 30, 45])
        
        clusters = [random.randint(5, 10), random.randint(14, 16), random.randint(18, 23)]
        dep_hour = random.choice(clusters)
        dep_min = random.choice([0, 15, 30, 45])
        dep_str = f"{dt.strftime('%Y-%m-%d')}T{dep_hour:02d}:{dep_min:02d}:00"
        
        dep_dt = datetime.fromisoformat(dep_str)
        # Skip past buses if date is today
        if dep_dt < datetime.now():
            continue

        arr_dt = dep_dt + timedelta(hours=int(dur_hours), minutes=dur_mins)
        
        bus_type = random.choice(bus_types)
        
        # Price: Approx ₹2.5 - ₹4 per KM based on type
        price_per_km = 2.5
        if "Sleeper" in bus_type: price_per_km += 0.8
        if "A/C" in bus_type: price_per_km += 0.6
        if "Volvo" in bus_type or "Scania" in bus_type: price_per_km += 0.5
            
        base_price = (distance * price_per_km) + random.randint(-50, 150)
        
        if base_price < 350: base_price = random.randint(350, 500)
            
        discount = int(base_price * 0.12)
        price = int(base_price - discount)
        
        buses.append({
            "operator": random.choice(operators),
            "bus_type": bus_type,
            "bus_no": f"UP{random.randint(10, 99)} {chr(random.randint(65, 90))}{chr(random.randint(65, 90))} {random.randint(1000, 9999)}",
            "from": source.title(),
            "to": dest.title(),
            "departure": dep_str,
            "arrival": arr_dt.strftime('%Y-%m-%dT%H:%M:%S'),
            "price": price,
            "original_price": int(base_price),
            "duration": f"{int(dur_hours)}h {dur_mins}m",
            "rating": round(random.uniform(3.5, 4.9), 1),
            "reviews": random.randint(50, 3000),
            "seats_left": random.randint(1, 25),
            "trips_covered": random.randint(100, 1500),
            "status": "Available"
        })
    
    buses.sort(key=lambda x: x["departure"])
    return buses

@app.route('/api/v1/trains')
def api_trains():
    org = request.args.get('org', '')
    dest = request.args.get('dest', '')
    date = request.args.get('date', '')
    return jsonify({"status": "success", "data": get_trains_api_data(org, dest, date)})

@app.route('/api/v1/buses')
def api_buses():
    org = request.args.get('org', '')
    dest = request.args.get('dest', '')
    date = request.args.get('date', '')
    trip_type = request.args.get('trip_type', 'oneway')
    return_date = request.args.get('return_date', '')
    
    result = {"status": "success", "data": get_buses_api_data(org, dest, date)}
    if trip_type == 'roundtrip' and return_date:
        result['return_data'] = get_buses_api_data(dest, org, return_date)
    return jsonify(result)

def get_real_trains_api(org, dest, date):
    """Fetches real-time train data from RapidAPI. Returns (data, error_message)"""
    # Using the specific host provided by the user
    url = "https://irctc1.p.rapidapi.com/api/v3/trainBetweenStations"
    headers = {
        "X-RapidAPI-Key": "7d9637a32cmsh6a89b1b195d11a1p131835jsn09535b581d7e",
        "X-RapidAPI-Host": "irctc1.p.rapidapi.com"
    }
    
    # Matching the irctc1.p.rapidapi.com parameter naming convention
    params = {
        "fromStationCode": org.upper(),
        "toStationCode": dest.upper(),
        "dateOfJourney": date # Format YYYY-MM-DD usually works here
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=12)
        
        # Monitor API usage in terminal
        rem = response.headers.get('X-RateLimit-Requests-Remaining', 'N/A')
        limit = response.headers.get('X-RateLimit-Requests-Limit', 'N/A')
        reset_seconds = response.headers.get('X-RateLimit-Requests-Reset', '0')
        
        # Human-readable reset
        import math
        try:
            rs = int(reset_seconds)
            h = math.floor(rs / 3600)
            m = math.floor((rs % 3600) / 60)
            s = rs % 60
            reset_str = f"{h}h {m}m {s}s"
        except:
            reset_str = "N/A"

        print(f"\n--- [TRAIN API STATUS] ---")
        print(f"Status: {response.status_code}")
        print(f"Remaining Calls: {rem} / {limit}")
        print(f"Reset in: {reset_str}")
        print(f"---------------------------\n")
        
        if response.status_code == 401 or response.status_code == 403:
            return None, "Invalid API Key or Unsubscribed Host. Please check your RapidAPI credentials."
        
        if response.status_code == 429:
            return None, f"Rate Limit Exceeded. You have reached your API call limit ({limit}) for today."

        if response.status_code == 200:
            data = response.json()
            # irctc1.p.rapidapi.com often returns data in a 'data' key or directly
            train_list = data.get('data', [])
            
            if not train_list:
                return [], None
                
            real_results = []
            for t in train_list[:12]:
                # Mapping the specific fields of irctc1 api
                train_class = random.choice(["SL", "3A", "2A", "1A"])
                # Realistic pricing based on MakeMyTrip / IRCTC standard routes
                class_prices = {
                    "SL": random.randint(150, 480),   # Sleeper
                    "3A": random.randint(520, 1150),  # 3rd AC
                    "2A": random.randint(1100, 1950), # 2nd AC
                    "1A": random.randint(1900, 3400)  # 1st AC
                }
                final_price = class_prices[train_class]
                
                dep_time_str = t.get('from_std', '10:00:00')
                arr_time_str = t.get('to_sta', '20:00:00')
                
                # Logic to detect next-day arrival
                arr_date = date
                if arr_time_str < dep_time_str:
                    # Arrives following day
                    start_dt = datetime.strptime(date, "%Y-%m-%d")
                    next_day = start_dt + timedelta(days=1)
                    arr_date = next_day.strftime("%Y-%m-%d")

                real_results.append({
                    "operator": t.get('train_name', 'Indian Railway'),
                    "train_no": t.get('train_number', '12345'),
                    "from": org.upper(),
                    "to": dest.upper(),
                    "departure": f"{date}T{dep_time_str}",
                    "arrival": f"{arr_date}T{arr_time_str}",
                    "price": final_price, 
                    "class": train_class,
                    "status": "Available",
                    "seats_available": random.randint(2, 60),
                    "departure_raw": f"{date}T{dep_time_str}",
                    "arrival_raw": f"{arr_date}T{arr_time_str}"
                })
            return real_results, None
        else:
            return None, f"API Error (Status {response.status_code}): {response.text[:100]}"
            
    except requests.exceptions.Timeout:
        return None, "API Request Timed Out. Please try again later."
    except Exception as e:
        return None, f"Unexpected error while fetching live data: {str(e)}"

# ==========================================
# Search logic consuming the APIs internally
# ==========================================
@app.route('/search-trains', methods=['POST'])
def search_trains():
    if 'user' not in session:
        return redirect('/')
        
    from_city = request.form.get('from_city', '').strip()
    to_city = request.form.get('to_city', '').strip()
    date = request.form.get('date', '')
    
    # Using Mock Data instead of real API
    trains_data = get_trains_api_data(from_city, to_city, date)
    
    for t in trains_data:
        t['departure_display'] = format_datetime(t['departure'])
        t['arrival_display'] = format_datetime(t['arrival'])
        t['departure_raw'] = t['departure']
        t['arrival_raw'] = t['arrival']

    no_match = len(trains_data) == 0

    return render_template("trains_results.html", 
                           from_city=from_city.upper(), 
                           to_city=to_city.upper(), 
                           trains=trains_data, 
                           no_match=no_match,
                           api_error=None)

@app.route('/search-buses', methods=['POST'])
def search_buses():
    if 'user' not in session:
        return redirect('/')
        
    from_city = request.form.get('leaving_from', '').strip()
    to_city = request.form.get('going_to', '').strip()
    date = request.form.get('date', '')
    trip_type = request.form.get('trip_type', 'oneway')
    return_date = request.form.get('return_date', '')
    
    try:
        buses_data = get_buses_api_data(from_city, to_city, date)
            
        if trip_type == 'roundtrip' and return_date:
            return_data = get_buses_api_data(to_city, from_city, return_date)
        else:
            return_data = []
            
        # Artificial delay to demonstrate the loader UI exactly like live APIs
        time.sleep(1.5)
        
        def format_bus_list(blist):
            filtered = []
            now = datetime.now()
            for b in blist:
                try:
                    dep_dt = datetime.fromisoformat(b['departure'])
                    if dep_dt < now:
                        continue
                except:
                    pass
                
                b['departure_display'] = format_datetime(b['departure'])
                b['arrival_display'] = format_datetime(b['arrival'])
                b['departure_raw'] = b['departure']
                b['arrival_raw'] = b['arrival']
                b['dep_time'] = datetime.fromisoformat(b['departure']).strftime('%H:%M')
                b['arr_time'] = datetime.fromisoformat(b['arrival']).strftime('%H:%M')
                filtered.append(b)
            return filtered
                
        buses_data = format_bus_list(buses_data)
        return_data = format_bus_list(return_data)
        no_match = len(buses_data) == 0
    except Exception as e:
        print("Bus API exception:", e)
        buses_data = []
        return_data = []
        error_msg = f"API Error Detected: {str(e)}"
        no_match = False

    return render_template(
        "buses_results.html", 
        from_city=from_city.title(), 
        to_city=to_city.title(), 
        buses=buses_data, 
        return_buses=return_data,
        trip_type=trip_type,
        no_match=no_match,
        api_error=error_msg if 'error_msg' in locals() else None
    )

@app.route('/enter-passenger', methods=['POST'])
def enter_passenger():
    if 'user' not in session:
        return redirect('/')

    session['flight_data'] = {
        "airline": request.form['airline'],
        "flight_no": request.form['flight_no'],
        "from_city": request.form['from_city'],
        "to_city": request.form['to_city'],
        "departure": request.form['departure'],
        "arrival": request.form['arrival'],
        "price": request.form['price'],
        "status": request.form['status']
    }

    return render_template("enter_passenger.html")

from decimal import Decimal

@app.route('/payment', methods=['POST'])
def payment():
    if 'user' not in session:
        return redirect('/')

    # Store passenger details in session
    phone_with_code = f"{request.form.get('country_code', '')} {request.form['mobile']}"
    session['passenger'] = {
        "name": request.form['name'],
        "age": request.form['age'],
        "gender": request.form['gender'],
        "mobile": phone_with_code,
        "email": request.form['email']
    }

    flight = session.get('flight_data')
    if not flight:
        return redirect('/home')

    base_fare = float(flight['price'])
    convenience_fee = 350.00
    total_amount = base_fare + convenience_fee
    
    session['checkout_total'] = total_amount

    return render_template("payment.html", base_fare=base_fare, convenience_fee=convenience_fee, total_amount=total_amount)

@app.route('/process-payment', methods=['POST'])
def process_payment():
    if 'user' not in session:
        return redirect('/')

    method = request.form['method']

    flight = session.get('flight_data')
    passenger = session.get('passenger')
    checkout_total = session.get('checkout_total')

    if not flight or not passenger or not checkout_total:
        return redirect('/home')

    price = Decimal(str(checkout_total))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        # ===================================
        # 💰 WALLET PAYMENT
        # ===================================
        if method == "Wallet":

            cursor.execute(
                "SELECT balance FROM wallet WHERE username=%s FOR UPDATE",
                (session['user'],)
            )
            wallet = cursor.fetchone()

            if not wallet:
                return "Wallet not found ❌"

            current_balance = Decimal(wallet['balance'])

            if current_balance < price:
                return "Insufficient Wallet Balance ❌"

            new_balance = current_balance - price

            cursor.execute(
                "UPDATE wallet SET balance=%s WHERE username=%s",
                (new_balance, session['user'])
            )

        # ===================================
        # 💳 CARD / UPI / NET BANKING
        # ===================================
        else:

            # Simulate payment success (90%)
            if random.randint(1, 10) == 1:
                return "Payment Failed ❌ Please Try Again"

        # ===================================
        # INSERT BOOKING AFTER SUCCESS
        # ===================================
        
        cursor.execute("""
            INSERT INTO bookings 
            (username, airline, flight_no, from_city, to_city,
             departure, arrival, price, status, booking_time,
             payment_method, payment_status, booking_status, refund_status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s)
        """, (
            session['user'],
            flight['airline'],
            flight['flight_no'],
            flight['from_city'],
            flight['to_city'],
            flight['departure'].replace("T"," "),
            flight['arrival'].replace("T"," "),
            price,
            flight['status'],
            method,
            "Success",
            "Confirmed",
            "Not Cancelled"
        ))

        booking_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO passengers (booking_id, name, age, gender, mobile, email)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            booking_id,
            passenger['name'],
            passenger['age'],
            passenger['gender'],
            passenger['mobile'],
            passenger['email']
        ))

        db.commit()

    except Exception as e:
        db.rollback()
        return f"Error: {str(e)}"

    finally:
        cursor.close()
        db.close()

    session.pop('flight_data', None)
    session.pop('passenger', None)

    flash("Booking Successful !")
    return redirect('/my-bookings')

@app.route('/cancel-booking', methods=['POST'])
def cancel_booking():
    if 'user' not in session:
        return redirect('/')

    booking_id = request.form['booking_id']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get booking details
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE id=%s AND username=%s
        """, (booking_id, session['user']))

        booking = cursor.fetchone()

        if not booking:
            return "Booking not found ❌"

        if booking['booking_status'] == "Cancelled":
            return redirect('/my-bookings')

        departure_time = booking['departure']
        booking_time = booking['booking_time']
        price = Decimal(booking['price'])

        now = datetime.now()

        # Rule 1: If departure < 2 hours → No refund
        if departure_time - now < timedelta(hours=2):
            refund_amount = Decimal(0)
            refund_status = "No Refund"

        # Rule 2: If cancelled within 24 hours of booking → Full refund
        elif now - booking_time <= timedelta(hours=24):
            refund_amount = price
            refund_status = " Full Refund"

        # Rule 3: Else → 80% refund
        else:
            refund_amount = price * Decimal("0.8")
            refund_status = "80% Refunded"

        # Update booking status
        cursor.execute("""
            UPDATE bookings 
            SET booking_status='Cancelled',
                refund_status=%s
            WHERE id=%s
        """, (refund_status, booking_id))

        # Credit wallet if refund applicable
        if refund_amount > 0:
            cursor.execute("""
                SELECT balance FROM wallet WHERE username=%s FOR UPDATE
            """, (session['user'],))

            wallet = cursor.fetchone()

            if wallet:
                new_balance = Decimal(wallet['balance']) + refund_amount

                cursor.execute("""
                    UPDATE wallet SET balance=%s WHERE username=%s
                """, (new_balance, session['user']))
            else:
    # If wallet row doesn't exist, create it
                cursor.execute("""
                    INSERT INTO wallet (username, balance)
                    VALUES (%s, %s)
                """, (session['user'], refund_amount))

        db.commit()

    except Exception as e:
        db.rollback()
        return f"Error: {str(e)}"
     
    finally:
        cursor.close()
        db.close()

    return redirect('/my-bookings')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
    