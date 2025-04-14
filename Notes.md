## Data_Engineering Challenge
This project demonstrates how to ingest data from a custom data ingestion module and stage it into an in-memory SQLite database. The focus is on handling customer details, tracking address changes over time, and maintaining postcode data—all while following best practices for data processing and database design.

## Overview
This project contains two modules, one for ingesting the data and the other for staging or loading the data into the database. It stages fully processed data from the data ingestion module into a normalized in-memory SQLite database. The goal is to manage:

Customer data: Includes fields such as email, first name, last name, sex, and date of birth.

Address history: Captures multiple addresses (street and postcode) per customer over time, with timestamp-based validity.

Postcode data: Stores supplemental postcode information.

By separating static (customer) and dynamic (address) data, the design supports tracking historical changes (e.g., when a customer moves) without overwriting existing records.

## Features
- In-memory Database: Uses SQLite for fast, temporary storage.

- Normalized Schema: Separates data into three tables:

    - Customers for static user details.

    - Addresses for address history with valid_from and valid_to fields.

    - Postcode for additional postcode details.

- Indexing: Creates indexes on key columns (e.g., email and user_id) to optimize query performance.

- Data Deduplication: Ensures unique customer records based on email addresses.

## Usage
- Data Ingestion Module:
The project depends on a module (e.g., data_ingestion.py) that provides a GetData class with a callmethods() function. This function should return a dictionary containing:

    - "customer_data": a DataFrame with columns email, first_name, last_name, sex, dateOfBirth, street, and postcode.

    - "postcode_data": a DataFrame containing postcode-related details.

- Run the Application:
The main script (e.g., contained in stage_data.py) creates an in-memory SQLite database, builds the tables, loads data (with deduplication to satisfy UNIQUE constraints), and outputs table contents for verification.

Run the script with: python stage_data.py

## Design and Implementation Details
- Table Creation:
The StageData.create_tables() method creates three tables (Customers, Addresses, and Postcode) and properly defines indexes and foreign keys.
Note: The foreign key in the Addresses table references Customers(user_id).

- Data Loading:
    - The save_to_database() method:

    - Loads postcode data directly.

    - Deduplicates customer data based on the email field using drop_duplicates as there were duplicates present.

    - Inserts customer records, then merges the auto-generated user_id back into the source data to prepare address records.

    - This setup or design caters for when a user changes address, it is possible to insert a new address data with current valid dates without deleting or updating the previous record/address. This make it very easy to track history.

## Querying:
The query_table() method demonstrates querying the tables to validate that the data has been loaded correctly. It also queries the tables to count how many distinct users (from the Customers table) currently reside in each local authority. In the schema, I assumed that the local authority is represented by the region column in the Postcode table. I also assumed that the current address for a user is the one with valid_to IS NULL in the Addresses table.