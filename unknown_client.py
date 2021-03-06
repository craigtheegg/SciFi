import hashlib


def _hash_password(password):
  return hashlib.md5(password).hexdigest()


class UnknownClient(object):
  """Represents the state of a non-logged in client."""
  _TEST_PASSWORD = 'abc'

  def __init__(self, many_players):
    self.state = 'welcome'
    self.name = None
    self._tmp_pass = None
    self._many_players = many_players

  def prompt(self, connection, text):
    """Prompt user for input."""
    connection.write(text)
    connection.prompt()

  def update(self, connection, text=''):
    """Update the unknown client state.

    Returns:
      Player object when ready to switch to a logged in state.
    """
    if self.state == 'welcome':
      connection.write('Connection to SciFi established...')
      self.prompt(connection, 'Existing account? yes/no')
      self.state = 'existing'
    elif self.state == 'existing':
      if text.lower() == 'yes' or text.lower() == 'y':
        self.prompt(connection, 'Name:')
        self.state = 'user'
      elif text.lower() == 'quit' or text.lower() == 'q':
        connection.disconnect()
        self.state = 'done'
      elif text[:4].lower() == 'test':
        self.name = text
        if self._many_players.does_exist_by_name(self.name):
          self.state = 'password'
          return self.update(connection, UnknownClient._TEST_PASSWORD)
        else:
          self._tmp_pass = UnknownClient._TEST_PASSWORD
          self.state = 'verify_newpassword'
          return self.update(connection, UnknownClient._TEST_PASSWORD)
      else:
        self.prompt(connection, 'Choose a username:')
        self.state = 'new'
    elif self.state == 'user':
      self.name = text
      if self._many_players.does_exist_by_name(self.name):
        self.prompt(connection, 'Password:')
        self.state = 'password'
      else:
        connection.write('User %s does not exist.' % self.name)
        self.prompt(connection, 'Existing account? yes/no')
        self.state = 'existing'
    elif self.state == 'password':
      hash = _hash_password(text)
      try:
        p = self._many_players.get_player_by_name(self.name)
        if p.password_hash != hash:
          raise ValueError('Wrong password!')
      except (IndexError, ValueError) as e:
        connection.write('Error: %s' % e)
        self.state = 'existing'
        self.prompt(connection, 'Existing account? yes/no')
      else:
        connection.write('Welcome back %s.' % self.name)
        self.state = 'done'
        return p
    elif self.state == 'new':
      self.name = text
      if self._many_players.does_exist_by_name(self.name):
        connection.write('That name is already in use.')
        self.prompt(connection, 'Choose a username:')
        self.state = 'new'
      else:
        self.prompt(connection, 'Password: ')
        self.state = 'newpassword'
    elif self.state == 'newpassword':
      if len(text) < 3:
        connection.write('Password is too short.')
        self.prompt(connection, 'Choose a password:')
      else:
        self._tmp_pass = text
        self.prompt(connection, 'Enter password again:')
        self.state = 'verify_newpassword'
    elif self.state == 'verify_newpassword':
      if self._tmp_pass != text:
        connection.write('Passwords do not match')
        self.prompt(connection, 'Password:')
        self.state = 'newpassword'
      elif self._many_players.does_exist_by_name(self.name):
        connection.write('That name is already in use.')
        self.state = 'new'
      else:
        connection.write('Welcome %s!' % self.name)
        self.state = 'done'
        return self._many_players.new_player(self.name, _hash_password(text))
    return None
