Check if the current stage is complete and ready to advance:

1. Run all tests and verify >95% coverage
2. Check all TODO items for current stage in todo.md
3. Run performance benchmarks
4. Verify all documentation is updated
5. Use gemini to review entire stage: `gemini -p "Review Stage $ARGUMENTS completion" -a`
6. Generate completion report
7. If all criteria met, advance to next stage
8. Update CLAUDE.md with new current stage