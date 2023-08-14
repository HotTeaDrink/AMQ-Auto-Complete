from selenium import webdriver
from decouple import config
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import random, time, sys, json, sqlite3, os

def is_json_element(element):
    """
    The function checks if a given element is a valid JSON object or not.
    
    :param element: The parameter "element" is a string that may or may not be a valid JSON element. The
    function "is_json_element" checks if the string is a valid JSON element and returns True if it is,
    and False otherwise
    :return: The function `is_json_element` returns a boolean value. It returns `True` if the input
    `element` can be decoded as a JSON object, and `False` otherwise.
    """
    try:
        json.loads(element)
        return True
    except json.JSONDecodeError:
        return False

# Define a custom expected condition for WebSocket frame received with specific parameters
class WebSocketFrameReceived:
    def __init__(self, method, params):
        """
        This is the constructor function for a class that initializes two instance variables, method and
        params.
        
        :param method: The method parameter is a string that represents the name of the method that
        needs to be called
        :param params: The `params` parameter is a dictionary or list of parameters that will be passed
        to the method specified in the `method` parameter. The specific format and content of the
        `params` parameter will depend on the requirements of the method being called
        """
        self.method = method
        self.params = params

    def __call__(self, driver):
        """
        This function extracts song information from a JSON payload and inserts it into a database if it
        does not already exist.
        
        :param driver: The Selenium WebDriver instance used to interact with a web browser
        :return: a boolean value - True or False.
        """
        logs = driver.get_log("performance")
        for log in logs:
            message = log.get("message", "")
            if self.method in message:
                try:
                    payload_data = json.loads(message)
                    payload_data = payload_data["message"]["params"]["response"]["payloadData"]
                    payload_data = payload_data[2:]

                    payload_json = json.loads(payload_data)
                    payload_json = payload_json[1]["data"]
                    
                    if isinstance(payload_json, dict):
                        # Extract the songInfo English parameter and the full URL parameter
                        english = payload_json["songInfo"]["animeNames"]["english"]
                        url = payload_json["songInfo"]["urlMap"]["catbox"]["720"]
                        
                        print("English:", english)
                        print("URL:", url)
                        
                        if english and url:
                            print("Inserting into database...")
                            try:
                                cursor.execute("INSERT OR IGNORE INTO songs VALUES (?, ?)", (english, url))
                                conn.commit()
                                print("Done.")
                            except sqlite3.IntegrityError:
                                print("Entry already exists.")
                                
                            return True
                        
                except (KeyError, ValueError):
                    pass
        return False
    
def print_network_logs(logs):
    """
    This function prints logs related to network activity during a quiz game and searches for specific
    URLs to extract answers from a database or wait for further information.
    
    :param logs: This function takes in a list of network logs as input. Each log is a dictionary
    containing information about a network request/response
    """
    for log in logs:
        network_log = json.loads(log["message"])["message"]
        
        try:
            if network_log.get("method") == "Network.webSocketFrameReceived":
                endQuiz = network_log.get("params", {}).get("response", {}).get("payloadData")
                endQuiz = endQuiz[2:]
                if not is_json_element(endQuiz):
                    pass
                else:
                    endQuiz = json.loads(endQuiz)
                    endQuiz = endQuiz[1]["command"]
                    if endQuiz == "quiz end result":
                        print("The Quiz has ended.")
                        print("----------------------------")
                        printed_urls.clear()
                        time.sleep(random.uniform(0.1, 0.5))
        except NoSuchElementException:
            pass

        if network_log.get("method") == "Network.responseReceived":
            url = network_log.get("params", {}).get("response", {}).get("url")
            if url.startswith('https://nl.catbox.video') and url not in printed_urls:
                printed_urls.add(url)
                url = url.replace("https://nl.catbox.video", "https://files.catbox.moe")
                print("----------------------------\n" + url)
                cursor.execute("SELECT * FROM songs WHERE url = ?", (url,))
                result = cursor.fetchone()
                
                if result:
                    print("Entry found.")
                    print("Answer: " + result[0])
                    time.sleep(random.uniform(0.1, 0.5))  # Random sleep time between 0.1 and 0.5 seconds
                    try:
                        wait = WebDriverWait(driver, 120)
                        qp_Answer_Input = wait.until(EC.element_to_be_clickable((By.ID, "qpAnswerInput")))
                        qp_Answer_Input.send_keys(result[0])
                        time.sleep(random.uniform(0.1, 0.5))  # Random sleep time between 0.1 and 0.5 seconds
                    except NoSuchElementException:
                        pass
                    
                else:
                    print("Entry not found.")
                    #Wait until the next Network.webSocketFrameReceived method is received with songInfo and Url parameters
                    wait = WebDriverWait(driver, 120)
                    wait.until(WebSocketFrameReceived("Network.webSocketFrameReceived", {"songInfo": True, "Url": True}))


# Connect to the database (creates a new database if it doesn't exist)
conn = sqlite3.connect('songs.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

url = 'https://animemusicquiz.com/'

caps = DesiredCapabilities.CHROME
caps['goog:loggingPrefs'] = {'performance': 'ALL'}
options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(desired_capabilities=caps, options=options)
driver.get(url)
time.sleep(2)

driver.find_element(By.ID, "loginUsername").send_keys(config('USER'))
time.sleep(random.uniform(0.5, 5))
driver.find_element(By.ID, "loginPassword").send_keys(config('MDP'))
time.sleep(random.uniform(0.5, 5))
driver.find_element(By.ID, "loginButton").click()
time.sleep(2)

try:
    # If the app can't reach the server shutdown the script
    cancel_button = driver.find_element(By.CLASS_NAME, "swal2-confirm")
    if cancel_button.is_displayed():
        print("Impossible to connect to the server: Stopping the script")
        cancel_button.click()
        driver.quit()
        os.system('cls')
        sys.exit()
except NoSuchElementException:
    print("swal2-confirm element not found: Continue")

try:
    already_online_continue_button = driver.find_element(By.ID, "alreadyOnlineContinueButton")
    if already_online_continue_button.is_displayed():
        print("Already online: Continue")
        already_online_continue_button.click()
        time.sleep(5)
except NoSuchElementException:
    print("alreadyOnlineContinueButton element not found: Continue")
    
time.sleep(5)
    
try:
    continue_button = driver.find_element(By.CLASS_NAME, "swal2-confirm")
    if continue_button.is_displayed():
        print("Pop-Up")
        continue_button.click()
        time.sleep(5)
except NoSuchElementException:
    print("swal2-confirm element not found: Continue")

printed_urls = set()

# Continuously fetch and print logs in real-time
while True:
    # Fetch the current logs
    logs = driver.get_log("performance")

    # Print new network logs
    print_network_logs(logs)

    # Wait for a brief moment before checking for new logs again
    time.sleep(1)