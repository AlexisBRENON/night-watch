import tinyweb


# Create web server application
app = tinyweb.webserver()


# Index page
@app.route("/")
async def index(request, response):
    await response.send_file("index.html")


# Another one, more complicated page
@app.route("/table")
async def table(request, response):
    # Start HTTP response with content-type text/html
    await response.start_html()
    await response.send(
        "<html><body><h1>Simple table</h1>"
        "<table border=1 width=400>"
        "<tr><td>Name</td><td>Some Value</td></tr>"
    )
    for i in range(10):
        await response.send("<tr><td>Name{}</td><td>Value{}</td></tr>".format(i, i))
    await response.send("</table>" "</html>")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
