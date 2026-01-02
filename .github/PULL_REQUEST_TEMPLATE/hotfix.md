---
name: 🔥 Hotfix Pull Request
about: Use this template for urgent production fixes
title: "[HOTFIX] "
labels: ["hotfix", "urgent", "production"]
assignees: []
---

## 🔥 Hotfix Pull Request

### 📋 Description
<!-- Provide a clear and concise description of the critical issue being fixed -->

### 🚨 Severity
- [ ] Critical (system down, data loss, security vulnerability)
- [ ] High (major functionality broken, significant user impact)
- [ ] Medium (important feature not working, moderate user impact)

### 🎯 Impact Assessment
**What is the impact of this issue?**
<!-- Describe the business/user impact -->

**How many users are affected?**
<!-- Estimate the scope of impact -->

**Is this blocking production deployment or causing downtime?**
- [ ] Yes
- [ ] No

### 🐛 What is the current behavior?
<!-- Describe the current broken behavior -->

### ✅ What is the new behavior?
<!-- Describe the expected behavior after the fix -->

### 🔍 What does this PR do?
<!-- Describe the changes made to fix the issue -->

### 🔄 Deployment Plan
**Target Environment:**
- [ ] Production
- [ ] Staging (for verification before production)

**Deployment Strategy:**
<!-- Describe how this will be deployed (e.g., immediate deployment, scheduled maintenance window, etc.) -->

**Rollback Plan:**
<!-- Describe how to rollback if issues arise -->

### 🧪 How has this been tested?
<!-- Please describe the tests that you ran to verify your fix -->

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing in staging environment
- [ ] Smoke tests
- [ ] Regression tests
- [ ] Other (please describe)

### ⚠️ Risk Assessment
**What are the risks of this fix?**
<!-- Describe potential side effects or risks -->

**What monitoring should be in place after deployment?**
<!-- Describe what metrics/alerts to watch -->

### 📝 Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] New and existing unit tests pass locally with my changes
- [ ] The issue has been reproduced and verified as fixed
- [ ] Code review has been completed (or expedited review process followed)
- [ ] Deployment plan has been communicated to stakeholders
- [ ] Rollback plan is documented and ready

### 🔗 Related Issues
<!-- Link to the critical issue -->
Fixes #(issue number)

### 📚 Additional Notes
<!-- Add any other context about the hotfix -->
<!-- Include any temporary workarounds, follow-up tasks, or technical debt created -->

### 👥 Stakeholders Notified
<!-- List who has been notified about this hotfix -->
- [ ] Product/Engineering Lead
- [ ] DevOps/Infrastructure Team
- [ ] Customer Support (if user-facing)
- [ ] Other: <!-- specify -->

