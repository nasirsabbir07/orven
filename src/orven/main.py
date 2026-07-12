import typer

app = typer.Typer()

@app.command()
def hello():
    """Test command."""
    print("Hello from Orven!")

if __name__ == "__main__":
    app()