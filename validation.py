import re

def valid(username, password, verify, email):
	USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
	PW_RE = re.compile(r"^.{3,20}$")
	EMAIL_RE=re.compile(r"^[\S]+@[\S]+\.[\S]+$")
	user_error, password_error, verify_error, email_error = False, False, False, False
	if not USER_RE.match(username):
		user_error=True
	if not PW_RE.match(password):
		password_error=True
	if not password==verify:
		verify_error=True
	if not EMAIL_RE.match(email) and not email=="":
		email_error=True
	return user_error, password_error, verify_error, email_error
	 #If it is correct, will yield False

