# Module 00: Introduction

## Objective

Frame the two-day workshop around a governed readmissions and discharge-planning agent pattern.

## Key concepts

1. Healthcare agents require explicit trust boundaries.
2. RAG does not replace policy, authorization, or human review.
3. Hosted agents need supply-chain, deployment, and telemetry controls.
4. Human review is part of the architecture.

## Scenario

A care manager or ADT nurse opens a synthetic tomorrow-discharge worklist. The agent retrieves approved protocols, relevant case context, and an approved risk-score response, then drafts a transition-exception packet and creates a human review task. The human reviewer approves, edits, rejects, escalates, or requests rework.

## Safety boundaries

The agent does not make clinical determinations, state that a patient is safe to discharge, or alter discharge orders.
