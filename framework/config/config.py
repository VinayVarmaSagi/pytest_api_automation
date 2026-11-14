import os
from pathlib import Path
from dotenv import dotenv_values


ENV = os.environ.get("ENV", "dev")#fetches ENV=QA for ex from terminal , else default to dev
BASE_DIR = Path(__file__).resolve().parent.parent  # config.py's folder → up to framework/  # points to framework/config/, no matter where you run from
#__file is current directory, resolve gives absolute path
#Path(__file__).resolve().parent gets you framework/config/ (where config.py lives). One more .parent walks up to framework/ — where your .env files actually are.
#BASE_DIR helps us get absolute path ie users/vinay/projects/framework/config/config.py , relative is .env inside the folder where im currently in.
#if we run tests from different folders then this relative path may not work everytime

#print("BASE_DIR:", BASE_DIR)
#print("dev file exists:", (BASE_DIR / ".env").exists())
#print("qa file exists:", (BASE_DIR / f".env.{os.environ.get('ENV','dev')}").exists())

#os.environ gets the dictionary of env variables that python process can see. anything in this visible to every file in the project. os.environ is the raw input, and config.py is the only file that reads it. Everything else imports the clean, typed constants.
#python-dotenv gives two ways to read file
#load_dotenv() reads file and immediately write every key into os.environ, we dont get a chance to look at the values or combine them with anything first
#dotenv_values() reads file and just hands us back a plain dict, os.environ stays untouched
#we need that pause because we want to merge two files

base_values = dotenv_values(BASE_DIR / ".env")#loads the file like a dictionary. this file has information which is applicable to every environment(ex timeout), env_values has only those specific to that env(ex url for each env)
env_values = dotenv_values(BASE_DIR / f".env.{ENV}")#if this file is not found, it doesnt error but just give empty {}, so it quietly gets base values

merged = {**base_values, **env_values}#order matters - if both are present, later takes precendence ie env_values
#** unwraps to dictionary, if both dicts have same key then the later wins

for key, value in merged.items():
    os.environ.setdefault(key, value)#it’s set only if the key isn’t in os.environ at all. sending token from env variables sets that value since its value is not present anywhere
#precedence is Terminal/CI Env variable >> .env.{ENV} >> .env >> Hardcoded default in the lines below
#setdefault is method in dictionary
#if we dont send Token from terminal ex pytest , then it sets default from base values and gets token
#if we send token from terminal ex export TOKEN=my-real-token pytest, default doesnt need to set it hence it skips. because usually CI secrets gets injected from runtime in GHA/Jenkings but not pushed to github. since its sent from terminal os.environ already has it
#if we send value from terminal here token, the os.environ already has it hence it doesnt set it again. but if that value is not sent via terminal - os.environ tries to set the value from merged_values ie either from base_values, env_values

BASE_URL = os.environ.get("BASE_URL", "https://gorest.co.in/")
TOKEN = os.environ.get("TOKEN")#default value is empty as we want to get from terminal or CI, We shouldnt hardcode. if token is none, fail loudly instead of later tests failing because of 401
if not TOKEN: raise RuntimeError("TOKEN not set")
#if not TOKEN is true when TOKEN is None (not set anywhere) or "" (set but empty).
#raise stops execution immediately and shows your message.
TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", 120))
EXISTING_USER = int(os.environ.get("EXISTING_USER", 8615349))
MAX_RESPONSE_TIMEOUT = int(os.environ.get("MAX_RESPONSE_TIMEOUT", 2000))

#note: this file is framework's config loader to pull values from .env , terminal(environment variables) to python constants  so that the tests can import these values directly without hardcoding them in the tests. if env file gets changed, update just in config and tests are untouched
#sequence :
#1.Python starts. os.environ already holds anything set in the terminal or CI.
#2.Pick the environment. Read ENV, defaulting to dev.
#3.Read both files. Load .env into base_values and .env.<ENV> into env_values.
#4.Merge. merged = {**base_values, **env_values}, so the env-specific file wins on duplicate keys.
#5.Fill the gaps. For each key in merged, setdefault adds it to os.environ only if it isn’t already there, so terminal values are never overwritten(because terminal values are already present in os.environ).
#6.Build constants. os.environ.get() reads each value into a Python constant, with type conversion and a fallback default.
#7.Tests import the constants. No hardcoding, and the same tests run against any environment.

#The sequence (same every run)
#Python starts. os.environ already has whatever you typed in the terminal.
#ENV picks the file. No ENV in the terminal means dev, so .env.dev is read. ENV=qa means .env.qa.
#Both files are read and merged. The env file wins over .env for the same key.
#setdefault fills the gaps. It adds file values to os.environ only for keys not already there, so the terminal always wins.
#get reads the final value into the constant. If the key exists nowhere, the hardcoded default is used. int() then converts it to a number where needed.