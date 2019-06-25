if False:
    import webapp

class Handler:
    app: 'webapp.FHApp' = None

    def __init__(self, app: 'webapp.FHApp'):
        self.app = app
