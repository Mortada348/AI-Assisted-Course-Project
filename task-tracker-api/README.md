# Task Tracker API

A small learning-focused REST API built with **FastAPI** and **Pydantic**,
using local **JSON file storage** instead of a database (see `ADR-001`).
The API is consumed by a separate web frontend.

This is a starting skeleton: it currently exposes only a `/health` endpoint.
Task-related endpoints (create, view, filter, update, assign, validate,
delete) will be added on top of this structure.

## Project structure
