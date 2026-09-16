import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/landslide_db")
cur = conn.cursor()

# 1. Geometry and location of Dehradun High Risk Slopes
cur.execute("SELECT id, name, risk_level, ST_AsText(boundary), ST_SRID(boundary) FROM risk_zones WHERE name = 'Dehradun High Risk Slopes';")
rows = cur.fetchall()
print("Dehradun High Risk Slopes Record:")
for r in rows:
    print(f"  ID: {r[0]}, Name: {r[1]}, Level: {r[2]}")
    print(f"  Geometry WKT: {r[3]}")
    print(f"  SRID: {r[4]}")

# 2. Check if (30.529505, 79.085957) lies inside Dehradun High Risk Slopes
lat = 30.529505
lon = 79.085957
cur.execute("""
    SELECT name,
           ST_Contains(boundary, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS contains_point,
           ST_Distance(boundary::geography, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000.0 AS distance_km
    FROM risk_zones
    WHERE name = 'Dehradun High Risk Slopes';
""", (lon, lat, lon, lat))
row = cur.fetchone()
print("\nPoint-in-Polygon Check for Kedarnath (30.529505, 79.085957):")
print(f"  Inside Dehradun Zone: {row[1]}")
print(f"  Distance from Zone  : {row[2]:.2f} km")

# 3. Check point inside Dehradun (30.42, 78.42)
cur.execute("""
    SELECT name,
           ST_Contains(boundary, ST_SetSRID(ST_MakePoint(78.42, 30.42), 4326)) AS contains_point
    FROM risk_zones
    WHERE name = 'Dehradun High Risk Slopes';
""")
row_deh = cur.fetchone()
print(f"\nPoint-in-Polygon Check for Dehradun Interior Point (30.42, 78.42):")
print(f"  Inside Dehradun Zone: {row_deh[1]}")

cur.close()
conn.close()
