import pandas as pd
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all routes coming from specific origin
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
  
# Database connection details
credentials={
    "DB_HOST":"localhost",
    "DB_PORT":5432,
    "DB_NAME":"MoviesDataset",  # Replace with your actual database name
    "DB_USER":"postgres",      # Replace with your PostgreSQL username
    "DB_PASSWORD":"admin"  # Replace with your PostgreSQL password
}
connection = None
cursor = None

# all of the movie data read in from file
movie_data = []  # List to store movie data as dictionaries (maps)

# Create the database connection
def create_database_connection():
    global connection, cursor  # Make sure to use global variables

    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host=credentials["DB_HOST"],
            port=credentials["DB_PORT"],
            database=credentials["DB_NAME"],
            user=credentials["DB_USER"],
            password=credentials["DB_PASSWORD"]
        )

        # Create a cursor object to execute queries
        cursor = connection.cursor()
        print("Connection successful!")

        # Example query to test the connection
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Database version: {db_version[0]}")

    except Exception as e:
        print(f"Error: {e}")

# Close the database connection
def close_database_connection():
    global connection, cursor
    if connection:
        cursor.close()
        connection.close()
        print("Connection closed.")

# Check if the table exists, if not, create it
def check_if_table_exists():
    create_database_connection()
    create_table_query = """
        CREATE TABLE IF NOT EXISTS Movies (
            id SERIAL PRIMARY KEY, -- Auto-incrementing ID for each row
            title TEXT NOT NULL, -- Title of the movie
            us_gross NUMERIC, -- US gross revenue (in dollars)
            worldwide_gross NUMERIC, -- Worldwide gross revenue (in dollars)
            production_budget NUMERIC, -- Production budget (in dollars)
            release_date TEXT, -- Release date of the movie
            distributor TEXT, -- Distributor company
            source TEXT, -- Source material (e.g., remake, original)
            major_genre TEXT, -- Genre of the movie
            creative_type TEXT, -- Creative type (e.g., historical fiction)
            director TEXT, -- Director of the movie
            rotten_tomatoes_rating REAL, -- Rotten Tomatoes rating (percentage)
            imdb_rating REAL, -- IMDB rating (out of 10)
            imdb_votes NUMERIC -- Number of votes on IMDB
        );
    """
    cursor.execute(create_table_query)
    connection.commit()  # Commit the transaction
    close_database_connection()

# Read excel file for movie data and populate movie_data list with movies
def read_input_file(print_data=True):
    # Read the Excel file
    file_path = 'movies.xlsx'
    try:
        # Load the Excel file into a DataFrame
        df = pd.read_excel(file_path)

        # Iterate through rows and print each row
        # print("Printing data row by row:" if print_data else "")
        for index, row in df.iterrows():
            row_dict = row.to_dict()

            # Process numeric fields: if empty or unknown, set to None (NULL in DB)
            for key in ['US Gross', 'Worldwide Gross', 'Production Budget', 'Rotten Tomatoes Rating', 'IMDB Rating', 'IMDB Votes']:
                if pd.isna(row_dict.get(key)) or row_dict.get(key) in [None, 'Unknown', '']:
                    row_dict[key] = None  # Set to None if the value is invalid or missing

            movie_data.append(row_dict)  # Add the dictionary to the list
            
            if print_data:
                pass
                # print(row_dict)  # Convert the row to a dictionary for easier reading
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Please check the file path and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Populate the movies table with movie_data
def populate_movies_table():
    create_database_connection()
    # Check if the table is empty by running a simple count query
    cursor.execute("SELECT COUNT(*) FROM Movies;")
    row_count = cursor.fetchone()[0]  # Fetch the count of rows

    if row_count == 0:
        # Only read the input file (the excel sheet) if there are no currrent entries in the movies table
        read_input_file(print_data=False)

        print("Table is empty. Inserting data...")
        for movie in movie_data:
            insert_query = """
            INSERT INTO Movies (
                title, us_gross, worldwide_gross, production_budget, release_date,
                distributor, source, major_genre, creative_type, director,
                rotten_tomatoes_rating, imdb_rating, imdb_votes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (
                movie.get('Title'), movie.get('US Gross'), movie.get('Worldwide Gross'),
                movie.get('Production Budget'), movie.get('Release Date'),
                movie.get('Distributor'), movie.get('Source'), movie.get('Major Genre'),
                movie.get('Creative Type'), movie.get('Director'), 
                movie.get('Rotten Tomatoes Rating'), movie.get('IMDB Rating'), movie.get('IMDB Votes')
            ))
            connection.commit()  # Commit the transaction for inserts
        print("Data inserted successfully.")
    else:
        print("Table already has data. Skipping insertion.")
    close_database_connection()

# Clear the databse upon request
@app.route('/clearDatabase', methods=['GET'])
def clear_database():
    create_database_connection()
    cursor.execute("DELETE FROM movies;")
    connection.commit() 
    close_database_connection()
    
    print("Database was cleared!")
    return jsonify({"message": "Request received to clear DB. Database Cleared."})

# Populate the database upon request
@app.route('/populateDatabase', methods=['GET'])
def populate_database():
    check_if_table_exists()
    populate_movies_table()

    print("called populate database")
    return jsonify({"message": "Request received to populate DB. Database Populated."})

# Populate the database upon request
@app.route('/topTenGrossing', methods=['GET'])
def getHighestGrossingMovies():
    create_database_connection()
    sql_query="""
        Select * from movies where worldwide_gross is not null order by worldwide_gross desc limit 10;
    """
    cursor.execute(sql_query)
    top_ten = cursor.fetchall()
    close_database_connection()
    print("the following rows were returned: ", top_ten)
    return jsonify({"message": "Request received to populate DB. Database Populated.", "data": top_ten})


# Work on this
@app.route('/filterMovies', methods=['POST'])
def filter_movies():
    filters = request.json.get('filters', {})
    print(filters)
    return jsonify({"message": "Filters received", "filters": filters})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)