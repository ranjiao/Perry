# Runbooks

One file per recurring procedure. Required sections: **When to use**, **Steps**,
**Verification**, **Rollback**.

`Verification` is the section people skip and the one that makes a runbook
worth having: it is what tells an agent the procedure actually worked, rather
than that it ran to the end without erroring.

Check them with `bin/deliverable-lint runbooks`.
