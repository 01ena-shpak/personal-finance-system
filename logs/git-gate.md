# GIT-GATE Decision

## Conflict

A merge conflict occurred in src/finance.py because the manual-change and agent-change branches contained different implementations of the balance calculation.

## Decision

The implementation total_income - total_expenses was selected.

This decision is based on the rule defined in spec/idea.md, which states that the current balance is calculated as total income minus total expenses.
