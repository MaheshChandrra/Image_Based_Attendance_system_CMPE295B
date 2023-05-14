class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

users = {
    '1': User(1, 'user1', 'password1'),
    '2': User(2, 'user2', 'password2')
}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)
