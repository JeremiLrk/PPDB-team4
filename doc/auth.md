# Authentication And Account Access

NetRank uses a simple account flow:

- sign up
- email verification
- log in
- profile updates
- password reset

## Sign Up

During sign up, the app asks for:

- email
- password
- first and last name
- date of birth
- gender
- phone number

When sign up succeeds, NetRank sends a verification email. The new account is not meant to be used normally until that email step is completed.

## Log In

Logging in checks the email and password, then stores the access token in an HTTP-only cookie.

That means:

- the browser keeps the token
- JavaScript does not read the token directly
- the user stays signed in until they log out or the session expires

## Profile Updates

Signed-in users can update their profile details from the dashboard, including:

- first name
- last name
- date of birth
- gender
- phone number

They can also change their password from the same account area.

## Password Reset

If a user forgets their password, the app sends a reset link by email.

The link opens the reset-password flow in the frontend, and the new password is saved after the token is checked.

## Email Verification

The verification email contains a link back to the frontend.

When that link is opened, the backend marks the account as verified, which unlocks the normal login flow.
