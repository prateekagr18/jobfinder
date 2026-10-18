"""jobfinder — a daily scanner for Engineering Manager and Senior Engineer roles.

Flow: pull postings straight from company ATS boards (Greenhouse / Lever / Ashby)
→ keep only target-role titles → score each against your resume (ATS keyword
match + recruiter-callback likelihood) → write a ranked daily report with the
missing keywords to add before you apply.
"""

__version__ = "0.1.0"
