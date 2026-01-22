

USER_INFO = """SELECT u.id, u.username, u.email,
    (u.created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
    (u.updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist,
    ud.date_of_birth as dob,
    ud.full_name as full_name,
    ud.gender,
    pp.original_key as profile_pic,
    pp.thumbnail_key as profile_thumbnail,
    pp.profile_pic_id as profile_pic_id
FROM vi.users u 
LEFT JOIN vi.user_details ud ON ud.user_id = u.id
LEFT JOIN vi.profile_pictures pp  ON pp.user_id = u.id
WHERE u.id = %(id)s;"""

