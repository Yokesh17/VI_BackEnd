USERS_SELECT_ALL = f'''SELECT id, username, email, password,
                        (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                        (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                    FROM vi.users '''

USER_INFO = F'''SELECT id, username, email,
                    (created_at + INTERVAL '5 hours 30 minutes') AS created_at_ist,
                    (updated_at + INTERVAL '5 hours 30 minutes') AS updated_at_ist
                FROM vi.users WHERE id=:id'''










