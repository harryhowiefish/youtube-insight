# Use the official PostgreSQL image as the base image
FROM postgres:latest

# Set environment variables if necessary (e.g., the default username and password)
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=youtube

# Copy the SQL script into the container. The script should contain the SQL commands to create your tables.
COPY ./sql/table_create.sql /docker-entrypoint-initdb.d/

# When the container starts, the PostgreSQL entrypoint script will execute any .sql files found in /docker-entrypoint-initdb.d
