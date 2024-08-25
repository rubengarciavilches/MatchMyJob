# Keep track of more complex SQL Queries here.


# This is the call that checks for the ratings that are missing, gets pairs that don't have a job_id under rating.
missing_ratings = """
SELECT j.id, r.id FROM public.job as j
JOIN public.search_job as sj on sj.job_id = j.id
JOIN public.search as s on s.id = sj.search_id
JOIN public.resume as r on r.user_id = s.user_id
LEFT JOIN public.rating as rt on rt.job_id = j.id AND rt.resume_id = r.id
WHERE r.is_active = true
AND rt.job_id is Null
"""
