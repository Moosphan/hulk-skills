# Project Types

Choose one primary type, then weight sections accordingly.

## CLI Tool

Emphasize:

- installation
- command synopsis
- common command examples
- flags and options
- configuration files and env vars

De-emphasize:

- screenshots
- long architecture explanations near the top

Signals:

- `bin` field in `package.json`
- argument parsing libraries
- `--help` support
- command-oriented examples

## Frontend Library Or Component

Emphasize:

- what the component does
- install and import example
- usage snippet
- API or props reference
- demo or preview link if real

De-emphasize:

- deployment steps

Signals:

- exports intended for import
- component files
- example app or storybook

## Backend Service Or API

Emphasize:

- prerequisites
- env vars
- local run instructions
- API routes or integration surface
- deployment notes when supported by the repo

De-emphasize:

- UI marketing sections

Signals:

- server entrypoint
- HTTP framework
- route definitions
- `.env.example`

## Full-Stack Application

Emphasize:

- user-facing capability summary
- local setup
- frontend and backend startup flow
- required services
- screenshots only if real and available

De-emphasize:

- exhaustive low-level API detail in the main README

Signals:

- separate client and server apps
- database migrations
- multi-service dev scripts

## Developer Tool Or DevOps Utility

Emphasize:

- problem solved for engineers
- configuration examples
- automation or CI/CD integration
- constraints and expected environments

De-emphasize:

- end-user product messaging

Signals:

- build, test, deploy, lint, codemod, infra, or workflow automation focus

## Library Or SDK

Emphasize:

- install instructions
- minimal usage example
- supported environments
- core API surface
- compatibility notes

De-emphasize:

- deployment instructions

Signals:

- exported modules
- typed public API
- examples focused on integration by other developers
