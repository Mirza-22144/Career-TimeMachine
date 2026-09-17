from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limits for the two endpoints pen-test H-4 flags, counted per client
# address. Counts live in this process's memory, so each server instance
# counts separately and counts reset on restart.
#
# A journey creates one session (the frontend only calls this with no stored
# token or on "Generate Token"); 10 a minute still leaves room for several
# people behind one shared address, while stopping scripted session floods.
SESSION_CREATION_LIMIT = "10/minute"
# Each scenario accepts one answer and every answer triggers feedback
# generation; 30 a minute is far beyond what a person answering scenarios
# can submit, even several on one address.
RESPONSE_SUBMISSION_LIMIT = "30/minute"

limiter = Limiter(key_func=get_remote_address)
