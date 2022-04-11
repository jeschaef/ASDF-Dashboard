from flask_nav import Nav
from flask_nav.elements import Navbar, View

nav = Nav()

nav.register_element('top', Navbar(
    View('Home', 'main.index'),
    View('Register', 'auth.register'),
    View('Login', 'auth.login')
))
