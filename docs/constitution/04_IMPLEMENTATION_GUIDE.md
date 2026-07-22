# ALFA COS Phase 2 Implementation Guide

Version: 2.0

Status: Active

Depends On

- 01_MISSION.md
- 02_COGNITIVE_ARCHITECTURE.md
- 03_ENGINEERING_SPEC.md

---

# Objective

Transform Alfa COS v0.1 into Alfa COS Phase 2 without rewriting the project.

The implementation must evolve the existing repository.

Never create a second implementation.

Never duplicate existing modules.

Always extend before replacing.

---

# Implementation Philosophy

1. Preserve working code.

2. Improve architecture gradually.

3. Avoid breaking changes.

4. Prefer refactoring over rewriting.

5. Maintain backwards compatibility.

6. Every completed feature must compile.

7. Every completed feature must pass tests.

---

# Development Order

The implementation MUST follow this order.

Phase A

Foundation

↓

Phase B

Runtime

↓

Phase C

Memory

↓

Phase D

Cognition

↓

Phase E

Providers

↓

Phase F

Tools

↓

Phase G

Plugins

↓

Phase H

Desktop

↓

Phase I

Testing

↓

Release

Never change this order unless technically required.

---

# Phase A

Repository Cleanup

Tasks

Remove dead code

Remove duplicate configuration

Remove duplicate providers

Remove circular imports

Standardize imports

Improve folder structure

Verify tests

Expected Result

Stable repository.

---

# Phase B

Runtime

Implement

Runtime Manager

Lifecycle Manager

Scheduler

Execution Queue

Event Dispatcher

Context Manager

Execution Monitor

Responsibilities

Initialize

Start

Stop

Restart

Recover

Shutdown

---

# Phase C

Memory

Implement

Working Memory

Persistent Memory

SQLite Backend

Memory Manager

Memory Cache

Memory Summaries

Memory Retrieval

Memory Search

Memory Metadata

Memory Events

Never allow direct database access.

Everything passes through Memory Manager.

---

# Phase D

Cognition

Implement

Executive Controller

Decision Engine

Reflection Engine

Goal Manager

Planning Improvements

Task Tracking

Execution Graph

Future Learning Hooks

No AI provider should contain cognition.

---

# Phase E

Providers

Refactor provider layer.

Support

NVIDIA

OpenRouter

Mock

Ollama Interface

Future

OpenAI

Gemini

Claude

Every provider implements identical interface.

Provider switching requires no restart.

---

# Phase F

Tool Framework

Implement

Tool Registry

Tool Loader

Permission Manager

Execution Sandbox

Built-in Tools

Calculator

Filesystem

Shell

Python

HTTP

Future

Desktop APIs

Android APIs

Robotics APIs

---

# Phase G

Plugin Framework

Implement

Plugin Discovery

Plugin Metadata

Plugin Registry

Plugin Loader

Plugin Permissions

Plugin Configuration

Plugin Lifecycle

Hot Reload (future ready)

---

# Phase H

Desktop Application

Technology

PySide6

Views

Chat

Memory

Settings

Logs

Providers

Plugins

Timeline

Brain Inspector

Task Manager

Requirements

No business logic.

Only presentation.

Everything calls Cognitive Core.

---

# Phase I

Developer Experience

Improve

Logging

Configuration

Error Handling

Testing

Documentation

Performance Metrics

Developer Commands

---

# Required Folder Structure

prototype/

kernel/

runtime/

memory/

planner/

executive/

reflection/

learning/

provider/

plugins/

tools/

desktop/

config/

common/

tests/

docs/

---

# Required Interfaces

Kernel

Runtime

Memory

Provider

Planner

Reflection

Learning

Plugin

Tool

Configuration

Logger

Every module communicates through interfaces.

---

# Dependency Rules

Allowed

Kernel

↓

Runtime

↓

Executive

↓

Planner

↓

Memory

↓

Providers

↓

Tools

Forbidden

UI → Provider

UI → Memory

Provider → UI

Plugin → Core modification

Tool → Kernel modification

---

# Coding Rules

Python 3.12

PEP8

Black

Ruff

Mypy

Type Hints

Docstrings

Dependency Injection

Composition

No Globals

No Hidden State

No Magic Strings

Constants centralized.

---

# Error Handling

Every public function

Must validate input.

Must catch expected failures.

Must log meaningful errors.

Must never expose secrets.

Recover whenever possible.

---

# Logging

Every module logs

Start

Finish

Duration

Errors

Warnings

Events

Never log

API Keys

Passwords

Tokens

Credentials

---

# Testing

Run pytest continuously.

Every new module

Unit Test

Integration Test

Regression Test

Performance Test (future)

Coverage should never decrease.

---

# Git Workflow

Main

↓

Development

↓

Feature Branch

↓

Pull Request

↓

Tests

↓

Merge

Never commit broken code.

---

# Documentation

Every module

README

Docstrings

Architecture Notes

Interface Definition

Usage Example

---

# Acceptance Criteria

Implementation succeeds only if

Repository builds.

Application starts.

Conversation works.

Planning works.

Memory works.

Reflection works.

Providers work.

Plugins load.

Tools execute.

Desktop launches.

Tests pass.

Documentation updated.

No duplicated architecture.

No circular imports.

---

# Final Deliverable

At completion Antigravity must provide

Architecture Summary

Files Added

Files Modified

Files Removed

Tests Executed

Performance Summary

Known Limitations

Roadmap for Phase 3

No intermediate reports.

Only final engineering report.

END OF DOCUMENT