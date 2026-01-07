
SUGGESTION_QUERY = """SELECT
    u.id,
    u.username,
    ud.full_name,
    ud.country,
    ud.profile_pic_dms,

    CASE 
        WHEN ud.country = cud.country THEN 1
        ELSE 0
    END AS same_location_score,

    COUNT(DISTINCT mf.connected_user_id) AS mutual_friends_count,
    COUNT(DISTINCT ci.interest) AS common_interests_count

FROM vi.users u
JOIN vi.user_details ud ON ud.user_id = u.id
JOIN vi.user_details cud ON cud.user_id = %(current_user_id)s

LEFT JOIN vi.user_connections c1
    ON c1.user_id = %(current_user_id)s
   AND c1.status = 'accepted'

LEFT JOIN vi.user_connections mf
    ON mf.user_id = u.id
   AND mf.connected_user_id = c1.connected_user_id
   AND mf.status = 'accepted'

LEFT JOIN vi.user_interests ui1
    ON ui1.user_id = %(current_user_id)s

LEFT JOIN vi.user_interests ci
    ON ci.user_id = u.id
   AND ci.interest = ui1.interest

WHERE u.id != %(current_user_id)s
AND u.id NOT IN (
    SELECT connected_user_id
    FROM vi.user_connections
    WHERE user_id = %(current_user_id)s
)

GROUP BY u.id, u.username, ud.full_name, ud.country, ud.profile_pic_dms, cud.country

ORDER BY
    same_location_score DESC,
    mutual_friends_count DESC,
    common_interests_count DESC

LIMIT %(limit)s;
"""


index_for_suggestion = """CREATE INDEX idx_user_details_country ON vi.user_details(country);
                CREATE INDEX idx_user_interests_user ON vi.user_interests(user_id);
                CREATE INDEX idx_user_interests_interest ON vi.user_interests(interest);
                CREATE INDEX idx_user_connections_user ON vi.user_connections(user_id);
                CREATE INDEX idx_user_connections_connected ON vi.user_connections(connected_user_id);
"""

SUGGESTION_MUTUAL_FRIENDS_QUERY = """SELECT
    su.id               AS suggested_user_id,
    su.username         AS suggested_username,

    mf.id               AS mutual_user_id,
    mf.username         AS mutual_username

FROM vi.users su
JOIN vi.user_details sud ON sud.user_id = su.id
JOIN vi.user_details cud ON cud.user_id = %(current_user_id)s

/* current user follows */
JOIN vi.user_connections c1
    ON c1.user_id = %(current_user_id)s
   AND c1.status = 'accepted'

/* suggested user is followed by same users */
JOIN vi.user_connections c2
    ON c2.user_id = su.id
   AND c2.connected_user_id = c1.connected_user_id
   AND c2.status = 'accepted'

JOIN vi.users mf ON mf.id = c1.connected_user_id

WHERE su.id != %(current_user_id)s

/* exclude already followed */
AND su.id NOT IN (
    SELECT connected_user_id
    FROM vi.user_connections
    WHERE user_id = %(current_user_id)s
)

ORDER BY su.id;
"""







