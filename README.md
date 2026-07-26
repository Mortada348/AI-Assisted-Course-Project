Task Tracker

A lightweight, self-hosted task tracking application for solo developers or small teams who want a single, shared task list without the overhead of user accounts, permissions, or real-time infrastructure.

Built with a Python/FastAPI backend and a simple HTML/CSS/JavaScript frontend.

Overview

Task Tracker is a simple, opinionated tool for managing a shared backlog of work. There's no login screen, no per-user data, and no real-time sync — just one task list that everyone with access to the app can view and update. It's designed to be easy to run locally or deploy on a small server, with a minimal footprint and no unnecessary complexity.

Target user: a solo developer or a small team that wants a shared, no-friction task list.

Features


Create tasks with:

Title
Description
Status (ToDo, InProgress, Done)
Priority (Low, Medium, High)
Assignee
Due date (with automatic overdue detection)
Tags



View all tasks in a list, with filtering by:

Status
Priority



Update tasks, including status transitions (e.g. ToDo → InProgress → Done)
Delete tasks


Out of Scope

The following are intentionally not part of this project:


Authentication / login
User accounts or per-user data
Multi-tenancy (multiple isolated teams/workspaces)
Real-time updates (e.g. WebSockets, live sync between clients)
A dedicated mobile app


This app assumes a single shared task list, accessed by trusted users, typically over a local network or a lightly-secured internal deployment (e.g. behind a VPN or reverse proxy if needed).
