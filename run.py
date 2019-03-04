from WebApplication.webapp import create_app

app = create_app()

if __name__ == '__main__':
    print("Server starting...")
    # app.run(debug=False)
    app.run(debug=True)
    print("Server started")

