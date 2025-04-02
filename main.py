from flask import Flask, redirect, request

from data import db_session

app = Flask(__file__)


def main():
    db_session.global_init("./db/blob.db")


if __name__ == "__main__":
    main()
    app.run("127.0.0.1", port=8080)
