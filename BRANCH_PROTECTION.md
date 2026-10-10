# Setting Up GitHub Branch Protection for Maintainer Approval

To guarantee that **all contributions must seek your explicit approval before being merged**, follow these simple steps once the repository is created on GitHub.

---

## Step-by-Step GitHub Branch Protection Setup

1. Open your repository on GitHub: `https://github.com/felixmwiya200/CALPHADHEACalc`
2. Click on **Settings** (top navigation bar of the repository).
3. In the left sidebar, under the **Code and automation** section, click on **Branches**.
4. Click the **Add branch protection rule** button (or click **Edit** next to `main`).
5. In the **Branch name pattern** field, enter:
   ```text
   main
   ```

6. Enable the following protection checkboxes:
   - [x] **Require a pull request before merging**
     - [x] **Require approvals**: Set to `1` (this means only you can approve PRs before they can be merged).
     - [x] **Dismiss stale pull request approvals when new commits are pushed**: Ensures that if a contributor pushes more changes after your review, it re-requires your approval.
     - [x] **Require review from Code Owners** (optional, if using a `CODEOWNERS` file).
   - [x] **Require status checks to pass before merging** (ensures automated CI tests pass before merging).
   - [x] **Require conversation resolution before merging** (ensures all your review comments are addressed).
   - [x] **Require linear history** (keeps the git commit log clean and readable).
   - [x] **Do not allow bypassing the above settings**: Enforces that nobody (not even collaborators) can force push or bypass the review gate.
   - [x] **Restrict who can push to matching branches**: Ensure only you (the repository owner) have write/push access.

7. Click **Create** (or **Save changes**) at the bottom of the page.

---

## How External Contributors Will Interact With Your Repository

1. **They cannot push directly to `main`**: Any attempt to run `git push origin main` by an external contributor will be rejected by GitHub with `Permission denied`.
2. **They must Fork and submit a Pull Request**: External users will fork your repository to their own account, make changes on a branch, and submit a PR to your upstream repository.
3. **You have 100% control**:
   - You will receive an email/notification for every new PR.
   - You can review the line-by-line diff, run tests, request changes, or leave comments.
   - You click **Merge** only if you approve. If you do not want the feature, you simply click **Close with comment** to decline.
