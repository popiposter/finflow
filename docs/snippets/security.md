# Security snippets

## Password hashing
Use pwdlib recommended hasher. Never implement custom hashing.

## Web auth
- short-lived access JWT
- longer-lived refresh JWT
- both issued by backend
- delivered via HttpOnly Secure cookies

## API tokens for Shortcut
- generate random token
- show once
- store only token hash
- allow revocation and last_used_at tracking
