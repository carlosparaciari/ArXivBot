#!/usr/bin/env python

import psycopg2
import os
import yaml
import sys

# This script will create a new user and database, and will create the tables
# needed for ArXivBot to work in this database. The tables are the following:
#
# 1. - Name : preferences
# 	 - Columns : ( user_identity integer , category text)
# 2. - Name : feedbacks
# 	 - Columns : ( message_time timestamp , user_identity integer , comment text )
# 3. - Name : errors
# 	 - Columns : (error_time timestamp, user_identity bigint, error_type text, details text)
# 4. - Name : chat
# 	 - Columns : (message_time timestamp , user_identity integer, content_type text, content text, query_identity bigint)

# NOTE 1 : You need to specify the user which can create a new user and a new database on your local server.
#		   For example, you could use the superuser credentials to do this:
#
#		   - user = 'postgres'
#		   - password = <the superuser password>
#
#          Insert this information below:

existing_user = 'postgres'
existing_pswd = ''

# Connect to PostgreSQL

try:
	conn = psycopg2.connect(user = existing_user, password = existing_pswd)
	conn.set_session(autocommit=True)
	print "Connection to PostgreSQ established."
except:
	print "ERROR: Impossible to connect to PostgreSQL. Please check the username and password provided."
	sys.exit()

cur = conn.cursor()

# Create a new user using the information stored in the yaml file with all the details of the bot.

# NOTE 2 : First of all, you need to create the yaml file where all details ArXivBot needs are stored.
#		   See the example yaml file in the ./Bot/Data/ folder.
#		   In the same folder create the file 'bot_details.yaml' and fill all the necessary
#		   fields as shown in the example yaml file.

import yaml

yamlfile_details = 'bot_details.yaml'

with open(os.path.join('Bot', 'Data', yamlfile_details), 'r') as file_input:
	detail = yaml.load(file_input)

try:
	sql_command = "CREATE USER " + detail['database_user'] + " WITH PASSWORD '" + detail['database_password'] + "';"
	cur.execute(sql_command)
	print "New PostgreSQL user created."
except:
	print "ERROR: Impossible to create a new user for PostgreSQL. Please check that the user connected to PostgreSQL can create new users."
	cur.close()
	conn.close()
	sys.exit()

# Create a database where the bot can save the information.

try:
	sql_command = "CREATE DATABASE " + detail['database_name'] + ";"
	cur.execute(sql_command)
	print "New database created."
except:
	print "ERROR: Impossible to create a new database for PostgreSQL. Please check that the user connected to PostgreSQL can create new database."
	cur.close()
	conn.close()
	sys.exit()

# Close connection with existing user.

cur.close()
conn.close()

# Start connection with newly create user.

try:
	new_conn = psycopg2.connect(dbname = detail['database_name'], user = detail['database_user'], password = detail['database_password'])
	print "Connection to new database established."
except:
	print "ERROR: Impossible to connect to PostgreSQL with the new user. Please check the existing user had privileges to create new users."
	sys.exit()

new_cur = new_conn.cursor()

# Create the four tables we need.

try:
	sql_command = "CREATE TABLE preferences ( user_identity integer , category text);"
	new_cur.execute(sql_command)
	print "Table 'preferences' created."
	sql_command = "CREATE TABLE feedbacks ( message_time timestamp , user_identity integer , comment text );"
	new_cur.execute(sql_command)
	print "Table 'feedbacks' created."
	sql_command = "CREATE TABLE errors (error_time timestamp, user_identity bigint, error_type text, details text);"
	new_cur.execute(sql_command)
	print "Table 'errors' created."
	sql_command = "CREATE TABLE chat (message_time timestamp , user_identity integer, content_type text, content text, query_identity bigint);"
	new_cur.execute(sql_command)
	print "Table 'chat' created."
except:
	print "ERROR: Impossible to create the tables. Please check the privileges of the new user."
	new_cur.close()
	new_conn.close()
	sys.exit()

# Close connection with new user.

new_conn.commit()
new_cur.close()
new_conn.close()