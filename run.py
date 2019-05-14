from webapp import create_app

app = create_app()

if __name__ == '__main__':
    print("Server starting.")
    # app.run(debug=False)
    app.run(host="152.66.170.159", debug=True)
    print("Server stopped.")
