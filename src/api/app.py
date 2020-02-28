from api.config import create_app
from api.resources import register_blueprints

app = create_app()
register_blueprints(app)

app.run(debug=True)
