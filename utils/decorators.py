def admin_only(admin_ids):
    def decorator(func):
        def wrapper(message):
            if message.from_user.id not in admin_ids:
                return
            return func(message)
        return wrapper
    return decorator