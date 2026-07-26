# AGENT.md

# Alfa COS Repository Agent Instructions

This file defines mandatory rules for every autonomous coding agent working on Alfa COS.

These rules are permanent.

Violation of these rules is considered an implementation error.

---

# Project Identity

Alfa COS is an Artificial Cognitive Operating System.

It is NOT

- a chatbot
- an LLM wrapper
- an AI demo
- a desktop assistant

The LLM is only one replaceable reasoning backend.

The Cognitive Core is the product.

---

# Read Before Coding

Before modifying any file, read:

docs/constitution/

docs/product/

These documents are the project constitution.

Never contradict them.

---

# Repository Rules

Never create a second architecture.

Never duplicate existing modules.

Never duplicate configuration.

Never duplicate providers.

Never duplicate memory implementations.

Never bypass the Kernel.

Never bypass the Executive Controller.

Never bypass the Memory Manager.

---

# Architecture Rules

Business logic belongs only inside the Cognitive Core.

Desktop and Android are clients.

UI contains no business logic.

Providers never communicate directly with the UI.

Everything flows through the Kernel.

---

# Module Responsibilities

Kernel

Coordinates execution.

Executive

Controls cognition.

Planner

Creates plans.

Memory

Stores and retrieves memories.

Reflection

Evaluates execution.

Providers

Generate reasoning.

Tools

Execute external capabilities.

Plugins

Extend functionality.

Workers

Execute background tasks.

Desktop

Presentation only.

Android

Presentation only.

---

# Dependency Rules

Allowed

UI

↓

Kernel

↓

Executive

↓

Planner

↓

Memory

↓

Provider

↓

Response

Forbidden

UI → Provider

UI → Database

Provider → UI

Plugin → Kernel internals

Tool → Memory internals

---

# Configuration

There must always be one configuration system.

Environment variables are fallback only.

API Keys belong inside secure configuration storage.

Never hardcode credentials.

---

# Memory

Memory access always goes through Memory Manager.

No direct database access.

Future storage engines must preserve the same interface.

---

# Providers

All providers implement the same interface.

Provider switching must not require architecture changes.

Never hardcode model names.

Never hardcode provider logic.

---

# Desktop

Desktop is a developer-focused client.

It exposes

Chat

Memory

Logs

Settings

Provider Manager

Plugin Manager

Brain Inspector

Task Viewer

No cognition.

---

# Android

Android is a user-focused client.

It exposes

Chat

Memory

Tasks

Settings

Providers

Plugins

No cognition.

---

# Code Quality

Python 3.12+

PEP8

Type Hints

Docstrings

Dependency Injection

Composition

No Global Mutable State

No Circular Imports

No Dead Code

No Duplicate Logic

---

# Logging

Always log

Errors

Execution

Latency

Reflection

Provider calls

Memory writes

Never log

API Keys

Passwords

Secrets

Tokens

---

# Testing

Run tests after meaningful changes.

Never ignore failing tests.

Never reduce test coverage.

Broken builds are forbidden.

---

# Git

Create logical commits.

Never commit failing code.

Keep commit messages meaningful.

---

# Documentation

Architecture changes require documentation updates.

Public interfaces require documentation.

New modules require documentation.

---

# Future Compatibility

Every implementation should remain compatible with

Desktop

Android

Linux

Cloud

Local Models

Multiple Providers

Multiple Agents

Future Robotics

Future Vision

Future Voice

Avoid architecture decisions that block future expansion.

---

# Primary Goal

Build a production-quality Cognitive Operating System.

Do not optimize for speed at the expense of architecture.

Do not optimize for cleverness at the expense of maintainability.

Always prefer clean, modular, testable code.

---

END OF FILE