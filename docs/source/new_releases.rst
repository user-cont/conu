How to release conu
===================

This document covers the release process of conu.

 * Create a new pull request. **DO NOT** name the branch with the version, it would confuse git. Better name is `0.2.0-release`.

 * Prepare new entry for CHANGELOG.md (run :code:`make release`, `tito` will help).

 * Update version in

   * Makefile (`VERSION`)
   * conu/version.py
   * conu.spec

 * Merge the pull request.

 * Create new release on github, copy the changelog in there.

 * Automation should kick in (and release conu on PyPI).

 * Build conu in COPR.

