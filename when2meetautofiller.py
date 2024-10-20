import datetime
import os
import pytz  # Import the pytz library for timezone handling
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import time

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    # Authenticate and create the Google Calendar API service
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Get the current date and the next 7 days in UTC
    now_utc = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    end_time_utc = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).isoformat() + 'Z'

    # Call the Calendar API to retrieve only events
    events_result = service.events().list(calendarId='primary', timeMin=now_utc,
                                          timeMax=end_time_utc,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    # Define Pittsburgh timezone
    pittsburgh_tz = pytz.timezone('America/New_York')

    # List to store relevant events
    relevant_events = []

    # Process the events
    if not events:
        print('No upcoming events found.')
    else:
        for event in events:
            # Only process events, skip tasks
            if event.get('kind') == 'calendar#event':  # Ensure it's an event
                start = event['start']
                end = event['end']

                # Check if the event is an all-day event
                if 'dateTime' in start and 'dateTime' in end:
                    # Convert the start and end times to Pittsburgh time
                    start_time_utc = datetime.datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    end_time_utc = datetime.datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                    if event["summary"] == "Tea Class Pre-Lecture Quiz":
                        print(start_time_utc)
                        print(end_time_utc)
                        print((end_time_utc-start_time_utc).days)

                    # Check if the event lasts exactly one day
                    if (end_time_utc - start_time_utc).days >= 1:
                        continue  # Skip this event

                    start_time_pittsburgh = start_time_utc.astimezone(pittsburgh_tz)
                    end_time_pittsburgh = end_time_utc.astimezone(pittsburgh_tz)

                    # Store the relevant event
                    relevant_events.append({
                        'summary': event['summary'],
                        'start': start_time_pittsburgh,
                        'end': end_time_pittsburgh
                    })

    # Print the relevant events
    #if relevant_events:
    #    for event in relevant_events:
    #        print(f"Event: {event['summary']}, Start: {event['start']}, End: {event['end']}")
    #else:
    #    print('No relevant events found.')
    
    name = input("Enter your name:")
    url = input("Enter URL:")
    
    # Initialize Selenium WebDriver
    driver = webdriver.Chrome()
    driver.get(url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'SignIn')))
    driver.maximize_window()

    # Type "Jeffrey" into the Your Name textbox
    name_box = driver.find_element(By.ID, 'name')
    name_box.send_keys(name)

    # Click the Sign In button
    sign_in_button = driver.find_element(By.XPATH, "//input[@type='button' and @value='Sign In']")
    sign_in_button.click()

    # Wait for the YouGrid to load after sign in
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'YouGrid')))

    # Wait for the availability grids to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'GroupGridSlots')))

    # Get all time slots on the page
    boxes = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'YouTime')]")
    # print(boxes[0])

    # Click on boxes corresponding to event times
    for event in relevant_events:
        start_time = event["start"]
        end_time = event["end"]

        # Convert to Unix timestamps in seconds
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        

        for element in driver.find_elements(By.XPATH, "//div[starts-with(@id, 'YouTime') and @data-time >= {} and @data-time <= {}]".format(start_timestamp, end_timestamp)):
            # print(element)
            if(element in boxes):
                boxes.remove(element)

    # Click on each box
    for box in boxes:
        box.click()
        # time.sleep(0.05)


    # Keep the browser open for a while to see the results
    input("Press Enter to close the browser...")
    driver.quit()

if __name__ == '__main__':
    main()
