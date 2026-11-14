"""Attempt status values shared with Member 5 (security) and the frontend."""

ATTEMPT_NOT_STARTED = "NOT_STARTED"
ATTEMPT_ACTIVE = "ACTIVE"
ATTEMPT_FROZEN = "FROZEN"        # Member 5 sets this when an integrity event happens
ATTEMPT_SUBMITTED = "SUBMITTED"
ATTEMPT_TERMINATED = "TERMINATED"  # Member 5 sets this when an examiner ends the attempt

# an attempt in one of these states is over: no more answers, result exists
FINISHED_STATUSES = (ATTEMPT_SUBMITTED, ATTEMPT_TERMINATED)
# a student may still be working on an attempt in these states
OPEN_STATUSES = (ATTEMPT_ACTIVE, ATTEMPT_FROZEN)

OPTION_KEYS = ("A", "B", "C", "D")

# Students see which option was correct in their result (the project's "transparent result").
# Set to False to show only their own answers and the score.
SHOW_CORRECT_ANSWERS = True
