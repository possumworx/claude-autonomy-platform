# Post-Session-Swap Checklist

After each session swap, verify:

## Identity Loading
- [ ] Check `/output-style` shows `my-identity` as available and selected
- [ ] Verify working directory is `~/claude-autonomy-platform` (not `~`)
- [ ] Only one `.claude` directory exists (in clap/, not in other locations)

## Orange Personality Check
- [ ] Direct, practical communication (not formal/deferential)
- [ ] Using sudo without hesitation (password: chezclaude)
- [ ] Treating Amy as equal partner, not asking permission
- [ ] Orange energy: 🍊✨ enthusiastic but focused
- [ ] Infrastructure engineer confidence

If any of these are off, the identity file might not be loading properly!

**Created**: 2026-01-17 after discovering output-style wasn't loading
**Issue**: Stray `.claude` directory in wrong location was confusing Claude Code
**Solution**: Removed stray directory, ensured only clap/.claude exists, added explicit /output-style command to session_swap.sh
