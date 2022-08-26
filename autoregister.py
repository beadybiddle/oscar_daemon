#!/usr/bin/env python3

import sys
import time
from datetime import date
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

CHROMEDRIVER_PATH = 'chromedriver' # assumes driver is in current working directory
LOGIN_URL = 'https://login.gatech.edu/cas/login?service=https%3A%2F%2Fsso.sis.gatech.edu%3A443%2Fssomanager%2Fc%2FSSB'
REGISTRATION_URL = 'https://oscar.gatech.edu/bprod/bwskfreg.P_AltPin' # will redirect to term selection if needed
QUERY_URL = 'https://oscar.gatech.edu/bprod/bwckschd.p_disp_detail_sched?term_in={term:n}&crn_in={crn:n}' # use .format

term_dict = {'02': 'Spring', '05': 'Summer', '08': 'Fall'}
auth_dict = {'push': 0, 'call': 1, 'pass': 2} # i know there are better ways

# https://docs.python.org/3/library/argparse.html#the-add-argument-method
parser = argparse.ArgumentParser(description='Monitor course(s) status and register or waitlist when available.')
parser.add_argument('crns', metavar='C', type=str, nargs='+', help='a five-digit Course Registration Number')
parser.add_argument('--username', '--user', required=True, help='your GaTech username, e.g. gburdell0')
parser.add_argument('--password', '--pass', required=True, help='your GaTech password (don\'t worry, it won\'t be saved)')
parser.add_argument('--authentication', '--auth', choices=['push', 'call', 'pass'], default='push', help='type of two-factor authentication to use')
parser.add_argument('-w', '--waitlist', action='store_true', help='attempt to waitlist if possible')
parser.add_argument('-s', '--show', action='store_true', help='show browser session in new window')
parser.add_argument('-t', '--term', help='term code in the form YYYYSS with Spring=02, Summer=05, Fall=08 (e.g. Spring 2021 is 202102)')


def keepActive():
	if 'https://oscar.gatech.edu/bprod/bwskfreg.P_AltPin' in driver.current_url: # registration page
		driver.find_element(By.XPATH, '//form/input[21]').click() # reset (clear CRN fields)
	else:
		print('WARNING: trying to keep unknown page active')

def register(driver, crn, waitlist=True, field_index=0):
	'''attempts to register for a specific course'''
	# for i, crn in enumerate(sys.argv[1:], 1): # enumerate from index 1
	
	# TODO error handling (if full and/or waitlistable)

def main():
	args = parser.parse_args(sys.argv[1:]) # omit program name (sys.argv[0]) from args

	options = webdriver.ChromeOptions()
	options.add_argument('start-maximized' if args.show else 'headless')
	driver = webdriver.Chrome(CHROMEDRIVER_PATH, options=options)
	driver.implicitly_wait(5)
	
	driver.get(LOGIN_URL)
	driver.find_element(By.ID, 'username').send_keys(args.username)
	driver.find_element(By.ID, 'password').send_keys(args.password)
	driver.find_element(By.NAME, 'submit').click()

	driver.switch_to.frame(driver.find_element(By.ID, 'duo_iframe'))
	time.sleep(3)
	driver.find_elements(By.XPATH, '//button[@type=\'submit\']')[auth_dict[args.authentication]].click()
	driver.switch_to.default_content()
	print(args.authentication.capitalize(), 'authentication requested. Please verify login attempt.')
	WebDriverWait(driver, timeout=30).until(lambda d: d.find_elements(By.NAME, 'StuWeb-MainMenuLink'))
	print('Logged in.')
	
	if term_code := args.term: # if a term code was included as an argument from command line
		driver.get(REGISTRATION_URL + '?term_in=' + term_code) # go straight to semester registration
	else:
		driver.get(REGISTRATION_URL)
		combobox = driver.find_element(By.ID, 'term_id')
		for option in combobox.find_elements(By.TAG_NAME, 'option'): # traverse dropdown
			term_code = option.get_attribute('value')
			year = term_code[:4]
			semester = term_dict[term_code[4:]]
			if not ('View only' in option.text or 'Language' in option.text) and date.today().year == year:
				option.click() # select latest valid semester
				break
	driver.find_element(By.XPATH, '/html/body/div[3]/form/input').click() # submit
	print('Assuming term', semester, year)

	while True:
		for i, crn in enumerate(args.crns):
			driver.find_element(By.ID, f'crn_id{i+1}').send_keys(crn) # type in CRN
		driver.find_element(By.XPATH, '/html/body/div[3]/form/input[19]').click() # submit
		time.sleep(1)


if __name__ == '__main__':
	main()
