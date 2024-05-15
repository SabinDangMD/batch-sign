import argparse
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main(username, password):
    # Setup headless mode for Chrome
    options = Options()
    options.add_argument("--headless=new")

    # Path to the ChromeDriver executable
    chromedriver_path = 'C:/Users/SabinDang/chromedriver.exe'
    c_service = ChromeService(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=c_service, options=options)

    # Log into Nextech
    driver.get('https://app1.intellechart.net/Eye/Login.aspx')

    # Fill in login details
    practice = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_cphMainBody_ui_TxtBxPractice"))
    )
    practice.send_keys("rcstl")
    
    usr = driver.find_element(By.ID, "ctl00_cphMainBody_ui_TxtBxUsername")
    usr.send_keys(username)
    
    pwd = driver.find_element(By.ID, "ctl00_cphMainBody_ui_TxtBxPassword")
    pwd.send_keys(password)
    
    login_button = driver.find_element(By.ID, "ctl00_cphMainBody_uiBtnLogin")
    login_button.click()

    # Navigate to Incomplete Chart page
    WebDriverWait(driver, 10).until(
        EC.url_to_be('https://app1.intellechart.net/Eye1/Pages/Notifications/IncompleteChart.aspx')
    )
    driver.get('https://app1.intellechart.net/Eye1/Pages/Notifications/IncompleteChart.aspx')

    # Store current window handle
    patient_list_window = driver.current_window_handle

    # Initialize counters
    stuck_chart_index = 0
    old_charts_left = 0
    charts_left = int(driver.find_element(By.CLASS_NAME, "k-pager-info").text.split(" ")[-2])

    # Process charts
    for i in range(charts_left):
        charts_left = int(driver.find_element(By.CLASS_NAME, "k-pager-info").text.split(" ")[-2])
        print(f"Charts Left: {charts_left}  Unable to sign charts: {stuck_chart_index}")

        if charts_left == old_charts_left:
            print("Error signing last chart, skipping it")
            stuck_chart_index += 1

        if charts_left < 1:
            print("No more charts to sign")
            sys.exit()

        # Select and open the first patient chart
        patient_chart = driver.find_elements(By.TAG_NAME, "a")[9 + stuck_chart_index]
        print(f"Processing chart {charts_left} ({patient_chart.text})")
        patient_chart.click()

        # Switch to the new window with patient summary
        patient_summary_window = WebDriverWait(driver, 10).until(
            EC.new_window_is_opened(driver.window_handles)
        )
        driver.switch_to.window(driver.window_handles[1])

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//img[@alt='Open IntelleChart Pro']"))
        ).click()

        icp_window = WebDriverWait(driver, 10).until(
            EC.new_window_is_opened(driver.window_handles)
        )
        driver.switch_to.window(driver.window_handles[2])

        # Handle user warning dialog if present
        if "User Warning" in driver.page_source:
            print(f"Chart # {charts_left} has a user warning dialog, attempting to clear it")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//mat-dialog-container[@id='mat-dialog-0']/icp-alert/mat-dialog-actions/button/span"))
            ).click()

        # Attempt to sign the chart
        try:
            sign_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fa-pencil"))
            )
            sign_button.click()
        except (ElementClickInterceptedException, TimeoutException):
            print(f"Unable to sign chart # {charts_left}, sign button not active")

        # Close the current chart window and return to the worklist
        driver.close()
        driver.switch_to.window(patient_summary_window)
        driver.close()
        driver.switch_to.window(patient_list_window)

        # Refresh the worklist
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "lbRefresh"))
        ).click()

        # Update the old charts left count
        old_charts_left = charts_left

    print(f"Unable to sign {stuck_chart_index} charts")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sign charts in Nextech automatically. Please verify that your charts have been reviewed for accuracy before running this command")
    parser.add_argument("--username", required=True, help="Username for Nextech login")
    parser.add_argument("--password", required=True, help="Password for Nextech login")
    args = parser.parse_args()

    main(args.username, args.password)
